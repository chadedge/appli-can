"""Map raw vendor dumps onto the master schema.

Each vendor gets an adapter that knows its shape; a detector picks the adapter;
``normalize_dataset`` walks an input root (one child per company, per the
input/ convention) and produces a single validated :class:`Dataset`.

Fields we recognize are normalized (via :mod:`applican.mappings`); the verbatim
value is kept in a ``*_raw`` companion; anything unrecognized is preserved in an
``extra`` bag so nothing is lost.
"""

from __future__ import annotations

import csv
import json
import pathlib
from typing import Any

from . import mappings as mp
from . import textparse
from .schema import Applicant, Application, Dataset, Screening, Skill, Source

_VENDOR_PREFIXES = {"workday", "greenhouse", "lever", "generic", "flattened",
                    "export", "dump", "candidate"}


def clean_company(name: str) -> str:
    """Turn a folder/file stem into a display company name.

    'workday_acme_corp' -> 'Acme Corp', 'initech_generic' -> 'Initech'.
    """
    tokens = [t for t in name.replace("-", "_").split("_") if t and t.lower() not in _VENDOR_PREFIXES]
    return " ".join(t.capitalize() for t in tokens) or name


# --- vendor detection --------------------------------------------------------

def _sniff_json_vendor(obj: Any) -> str | None:
    blob = json.dumps(obj).lower()
    if any(k in blob for k in ('"tenant"', '"requisitionid"', '"screeningtelemetry"')):
        return "workday"
    if any(k in blob for k in ('"export_type"', '"ai_match"', '"scorecards"')):
        return "greenhouse"
    return None


def detect_vendor(path: pathlib.Path) -> str | None:
    """Best-effort vendor/format identification for a file or company folder."""
    if path.is_dir():
        for jf in sorted(path.glob("*.json")):
            v = _sniff_json_vendor(json.loads(jf.read_text()))
            if v:
                return v
        return None
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in (".txt", ".pdf"):
        return "flattened_text"
    if suffix == ".json":
        return _sniff_json_vendor(json.loads(path.read_text()))
    return None


# --- adapters ----------------------------------------------------------------

def _rel(base: pathlib.Path, f: pathlib.Path) -> str:
    try:
        return str(f.relative_to(base.parent))
    except ValueError:
        return f.name


def from_workday(folder: pathlib.Path, company: str) -> tuple[Applicant, Source, list[Application]]:
    profile = json.loads((folder / "candidate_profile.json").read_text())
    history = json.loads((folder / "application_history.json").read_text())
    p = profile.get("profile", {})
    loc = p.get("contact", {}).get("location", {})

    # Workday parses the resume once at the candidate level; carry those skills
    # onto each application's screening block.
    parsed = profile.get("parsedResume", {})
    skills = [
        Skill(name=s["skill"].lower(), confidence=s.get("confidence"),
              baseline_match=s.get("baselineMatch"))
        for s in parsed.get("Parsed_Skills", [])
    ]

    applicant = Applicant(
        full_name=" ".join(v for v in (p.get("legalName", {}).get("first"),
                                        p.get("legalName", {}).get("last")) if v) or None,
        emails=[e for e in [p.get("contact", {}).get("primaryEmail")] if e],
        phone=p.get("contact", {}).get("phone"),
        location=", ".join(v for v in (loc.get("city"), loc.get("state")) if v) or None,
        ca_resident=p.get("consentFlags", {}).get("ccpaResident"),
        extra={"parsed_resume": parsed, "overall_inference": profile.get("automatedInferences", {})},
    )

    apps: list[Application] = []
    src_file = _rel(folder, folder / "application_history.json")
    for a in history.get("applications", []):
        tel = a.get("screeningTelemetry", {})
        stage = mp.map_stage(a.get("StageReached"))
        extra = {k: tel[k] for k in ("autoAdvanced", "note") if k in tel}
        apps.append(Application(
            company=company, role_title=a.get("jobTitle", "Unknown"),
            requisition_id=a.get("requisitionId"),
            applied_date=mp.parse_date(a.get("appliedOn")), applied_date_raw=a.get("appliedOn"),
            dispositioned_date=mp.parse_date(a.get("dispositionedOn")),
            dispositioned_date_raw=a.get("dispositionedOn"),
            stage_reached=stage, stage_reached_raw=a.get("StageReached"),
            outcome=mp.map_outcome(a.get("DispositionReason"), stage),
            disposition_raw=a.get("DispositionReason"),
            screening=Screening(
                match_score=mp.normalize_score(tel.get("matchScorePercent")),
                match_score_raw=tel.get("matchScorePercent"),
                fit_tier_raw=tel.get("Fit_Tier"), fit_quality=mp.fit_quality(tel.get("Fit_Tier")),
                parsed_skills=skills,
                keyword_hits=tel.get("keywordHits"), keyword_misses=tel.get("keywordMisses"),
            ),
            source_vendor="workday", source_file=src_file, extra=extra,
        ))

    source = Source(company=company, ats_vendor="workday",
                    source_files=sorted(_rel(folder, f) for f in folder.glob("*.json")))
    return applicant, source, apps


def from_greenhouse(file: pathlib.Path, company: str) -> tuple[Applicant, Source, list[Application]]:
    if file.is_dir():  # dump delivered as a folder — find the JSON export inside
        file = next(f for f in sorted(file.glob("*.json"))
                    if _sniff_json_vendor(json.loads(f.read_text())) == "greenhouse")
    data = json.loads(file.read_text())
    c = data.get("candidate", {})
    applicant = Applicant(
        full_name=" ".join(v for v in (c.get("first_name"), c.get("last_name")) if v) or None,
        emails=[e["value"] for e in c.get("email_addresses", []) if e.get("value")],
        phone=next((ph["value"] for ph in c.get("phone_numbers", []) if ph.get("value")), None),
    )

    apps: list[Application] = []
    for a in data.get("applications", []):
        m = a.get("ai_match", {})
        stage = mp.map_stage(a.get("current_stage"))
        disposition = a.get("rejection_reason") or a.get("status")
        extra = {"scorecards": a["scorecards"]} if a.get("scorecards") else {}
        apps.append(Application(
            company=company, role_title=a.get("job_name", "Unknown"),
            requisition_id=str(a["application_id"]) if a.get("application_id") else None,
            applied_date=mp.parse_date(a.get("applied_at")), applied_date_raw=a.get("applied_at"),
            dispositioned_date=mp.parse_date(a.get("rejected_at")),
            dispositioned_date_raw=a.get("rejected_at"),
            stage_reached=stage, stage_reached_raw=a.get("current_stage"),
            outcome=mp.map_outcome(disposition, stage), disposition_raw=disposition,
            screening=Screening(
                match_score=mp.normalize_score(m.get("match_score")),
                match_score_raw=m.get("match_score"),
                fit_tier_raw=m.get("match_tier"), fit_quality=mp.fit_quality(m.get("match_tier")),
                parsed_skills=[Skill(name=s.lower()) for s in m.get("parsed_keywords_matched", [])],
            ),
            source_vendor="greenhouse", source_file=file.name, extra=extra,
        ))
    return applicant, Source(company=company, ats_vendor="greenhouse", source_files=[file.name]), apps


def _to_bool(v: str | None) -> bool | None:
    if v is None:
        return None
    return v.strip().lower() in ("yes", "true", "1")


def from_csv(file: pathlib.Path, company: str) -> tuple[Applicant, Source, list[Application]]:
    applicant = Applicant()
    apps: list[Application] = []
    with open(file, newline="") as fh:
        for row in csv.DictReader(fh):
            if not applicant.full_name:
                applicant.full_name = row.get("candidate_name") or None
                if row.get("candidate_email"):
                    applicant.emails = [row["candidate_email"]]
            stage = mp.map_stage(row.get("last_stage"))
            disposition = row.get("disposition")
            skills = [s.lower() for s in (row.get("skills_parsed") or "").split(";") if s]
            apps.append(Application(
                company=company, role_title=row.get("position", "Unknown"),
                requisition_id=row.get("req_id"),
                applied_date=mp.parse_date(row.get("date_applied")),
                applied_date_raw=row.get("date_applied"),
                stage_reached=stage, stage_reached_raw=row.get("last_stage"),
                outcome=mp.map_outcome(disposition, stage), disposition_raw=disposition,
                screening=Screening(
                    match_score=mp.normalize_score(row.get("match_pct")),
                    match_score_raw=row.get("match_pct"),
                    fit_tier_raw=row.get("fit_rating"), fit_quality=mp.fit_quality(row.get("fit_rating")),
                    parsed_skills=[Skill(name=s) for s in skills],
                    auto_screened=_to_bool(row.get("auto_screened")),
                ),
                source_vendor="csv", source_file=file.name,
            ))
    return applicant, Source(company=company, ats_vendor="generic-csv", source_files=[file.name]), apps


def from_flattened_text(file: pathlib.Path, company: str) -> tuple[Applicant, Source, list[Application]]:
    blocks = textparse.parse_blocks(textparse.extract_text(file))
    applicant = Applicant()
    apps: list[Application] = []
    withheld = False
    for block in blocks:
        kv, raw = block["kv"], block["raw"].lower()
        if "withheld" in raw or "trade secret" in raw:
            withheld = True
        if "Candidate" in kv and "Position Applied" not in kv:
            applicant.full_name = kv.get("Candidate")
            if kv.get("Email on File"):
                applicant.emails = [kv["Email on File"]]
            applicant.phone = kv.get("Phone")
            applicant.location = kv.get("Resident State")
            applicant.ca_resident = (kv.get("Resident State", "").upper() == "CA") or None
        if "Position Applied" in kv:
            stage = mp.map_stage(kv.get("Furthest Stage"))
            disposition = kv.get("Final Disposition")
            note = kv.get("Disposition Note")
            # the note often carries the real reason; feed both to the mapper
            outcome = mp.map_outcome(" ".join(filter(None, [disposition, note])), stage)
            skills = [s.strip().lower() for s in (kv.get("Parsed Competencies") or "").split(",") if s.strip()]
            apps.append(Application(
                company=company, role_title=kv["Position Applied"],
                requisition_id=kv.get("Requisition"),
                applied_date=mp.parse_date(kv.get("Date Received")),
                applied_date_raw=kv.get("Date Received"),
                stage_reached=stage, stage_reached_raw=kv.get("Furthest Stage"),
                outcome=outcome, disposition_raw=disposition,
                screening=Screening(
                    match_score=mp.normalize_score(kv.get("Automated Match Score")),
                    match_score_raw=kv.get("Automated Match Score"),
                    fit_tier_raw=kv.get("System Fit Tier"),
                    fit_quality=mp.fit_quality(kv.get("System Fit Tier")),
                    parsed_skills=[Skill(name=s) for s in skills],
                    auto_screened=_to_bool(kv.get("Automation Screen Applied")),
                ),
                source_vendor="flattened_text", source_file=file.name,
                extra={"disposition_note": note} if note else {},
            ))
    return applicant, Source(company=company, ats_vendor="unknown (flattened PDF/text)",
                             source_files=[file.name], withholding_noted=withheld or None), apps


_ADAPTERS = {
    "workday": from_workday,
    "greenhouse": from_greenhouse,
    "csv": from_csv,
    "flattened_text": from_flattened_text,
}


# --- orchestration -----------------------------------------------------------

def _merge_applicant(into: Applicant, other: Applicant) -> Applicant:
    into.full_name = into.full_name or other.full_name
    into.emails = list(dict.fromkeys(into.emails + other.emails))
    into.phone = into.phone or other.phone
    into.location = into.location or other.location
    into.ca_resident = into.ca_resident if into.ca_resident is not None else other.ca_resident
    into.extra.update(other.extra)
    return into


def normalize_source(path: pathlib.Path) -> tuple[Applicant, Source, list[Application]] | None:
    """Detect and normalize one company's dump (a file or folder). None if unknown."""
    vendor = detect_vendor(path)
    if vendor not in _ADAPTERS:
        return None
    return _ADAPTERS[vendor](path, clean_company(path.stem if path.is_file() else path.name))


def normalize_dataset(root: pathlib.Path) -> tuple[Dataset, list[str]]:
    """Normalize every company dump under ``root`` into one Dataset.

    Returns the Dataset plus a list of human-readable warnings (skipped inputs).
    """
    applicant = Applicant()
    sources: list[Source] = []
    applications: list[Application] = []
    warnings: list[str] = []

    for child in sorted(root.iterdir()):
        if child.name.startswith(".") or child.name.lower() == "readme.md":
            continue
        result = normalize_source(child)
        if result is None:
            warnings.append(f"skipped (unrecognized vendor/format): {child.name}")
            continue
        appl, source, apps = result
        _merge_applicant(applicant, appl)
        sources.append(source)
        applications.extend(apps)

    return Dataset(applicant=applicant, sources=sources, applications=applications), warnings
