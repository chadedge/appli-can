"""Turn a normalized :class:`Dataset` into a per-company funnel report.

This is where the project pays off: it surfaces how far each application got, how
the software scored you, and — the point of the whole exercise — where automation
appears to have killed an application with no human in the loop.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Optional

from .mappings import stage_order
from .schema import Application, Dataset

# Below this, a disposition turnaround looks machine-made rather than human.
_INSTANT_SECONDS = 3600


def _parse_dt(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _turnaround(app: Application) -> tuple[Optional[float], str]:
    """Return (seconds_or_None, human_string) between applying and disposition.

    Prefers raw timestamps (which may carry time-of-day) over the date-only
    normalized fields, so a 118-second auto-reject isn't rounded to '0 days'.
    """
    start_dt, end_dt = _parse_dt(app.applied_date_raw), _parse_dt(app.dispositioned_date_raw)
    if start_dt and end_dt and (start_dt.time() != datetime.min.time() or end_dt.time() != datetime.min.time()):
        secs = (end_dt - start_dt).total_seconds()
        if secs < 120:
            return secs, f"{int(secs)}s"
        if secs < _INSTANT_SECONDS:
            return secs, f"{secs / 60:.0f}m"
        return secs, f"{secs / 86400:.1f}d"
    if isinstance(app.applied_date, date) and isinstance(app.dispositioned_date, date):
        days = (app.dispositioned_date - app.applied_date).days
        return days * 86400.0, f"{days}d"
    return None, "—"


def automation_reasons(app: Application) -> list[str]:
    """Why this application looks automation-driven (empty list = no signal)."""
    reasons: list[str] = []
    if app.outcome == "auto_rejected":
        reasons.append("outcome classified auto_rejected")
    if app.screening.auto_screened:
        reasons.append("auto-screen flag set")
    secs, human = _turnaround(app)
    if secs is not None and secs < _INSTANT_SECONDS and app.outcome not in ("active", "hired", "offer"):
        reasons.append(f"dispositioned {human} after applying")
    return reasons


def _company_apps(ds: Dataset, company: str) -> list[Application]:
    return [a for a in ds.applications if a.company == company]


def build_markdown(ds: Dataset, generated: Optional[str] = None) -> str:
    order = stage_order()
    apps = ds.applications
    out: list[str] = ["# Appli-CAN! Funnel Report", ""]
    stamp = f" on {generated}" if generated else ""
    out.append(f"_Generated{stamp} from {len(apps)} application(s) across "
               f"{len(ds.sources)} compan(ies) for {ds.applicant.full_name or 'you'}._")
    out.append("")

    # --- Overview ---
    outcomes = Counter(a.outcome or "unknown" for a in apps)
    flagged = [a for a in apps if automation_reasons(a)]
    withheld = [s for s in ds.sources if s.withholding_noted]

    out += ["## Overview", ""]
    out.append(f"- **Applications:** {len(apps)} across {len(ds.sources)} compan(ies)")
    out.append("- **Outcomes:** " + " · ".join(f"{k} {v}" for k, v in outcomes.most_common()))
    out.append(f"- ⚠️ **Automation implicated in {len(flagged)} of {len(apps)} application(s)** "
               "(see flags below).")
    if withheld:
        names = ", ".join(s.company for s in withheld)
        out.append(f"- 🔒 **{len(withheld)} compan(ies) admitted withholding data** under "
                   f"trade-secret/proprietary claims: {names}.")
    out.append("")

    # --- Per company ---
    out += ["## By company", ""]
    for src in ds.sources:
        capps = _company_apps(ds, src.company)
        out.append(f"### {src.company} — {src.ats_vendor}")
        scores = [a.screening.match_score for a in capps if a.screening.match_score is not None]
        reached = [order.get(a.stage_reached, -1) for a in capps if a.stage_reached]
        furthest = next((k for k, v in order.items() if v == max(reached)), "—") if reached else "—"
        out.append(f"- Furthest stage reached: **{furthest}**")
        if scores:
            out.append(f"- Match score: {min(scores):.0f}–{max(scores):.0f} "
                       f"(avg {sum(scores) / len(scores):.0f})")
        out.append("")
        out.append("| Role | Applied | Stage | Outcome | Score | Tier→q | Turnaround | Auto? |")
        out.append("|---|---|---|---|---|---|---|---|")
        for a in capps:
            s = a.screening
            _, human = _turnaround(a)
            auto = "⚠️" if automation_reasons(a) else ""
            tier = f"{s.fit_tier_raw}→{s.fit_quality}" if s.fit_tier_raw else "—"
            out.append(f"| {a.role_title} | {a.applied_date or a.applied_date_raw or '—'} "
                       f"| {a.stage_reached or '—'} | {a.outcome or '—'} "
                       f"| {s.match_score if s.match_score is not None else '—'} | {tier} "
                       f"| {human} | {auto} |")
        out.append("")
        # per-company automation notes
        notes = []
        for a in capps:
            reasons = automation_reasons(a)
            if reasons:
                extra_note = a.extra.get("note") or a.extra.get("telemetry_note") \
                    or a.extra.get("disposition_note")
                tail = f' — vendor note: "{extra_note}"' if extra_note else ""
                notes.append(f"  - **{a.role_title}**: {'; '.join(reasons)}{tail}")
        if notes:
            out.append("**Automation flags:**")
            out += notes
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def build_terminal(ds: Dataset) -> str:
    outcomes = Counter(a.outcome or "unknown" for a in ds.applications)
    flagged = sum(1 for a in ds.applications if automation_reasons(a))
    lines = [
        f"{len(ds.applications)} application(s) across {len(ds.sources)} compan(ies)",
        "outcomes: " + ", ".join(f"{k}={v}" for k, v in outcomes.most_common()),
        f"automation implicated in {flagged} application(s)",
    ]
    return "\n".join(lines)
