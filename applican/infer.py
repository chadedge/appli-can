"""Field & type discovery for raw vendor dumps (JSON and CSV).

The goal isn't validation — it's reconnaissance. Point this at a dump you've never
seen and it tells you what fields exist, their types, and which ones look like the
high-value screening telemetry worth normalizing into the master schema.
"""

from __future__ import annotations

import csv
from typing import Any

# Field names (normalized: lowercased, stripped of spaces/underscores) that map to
# the concepts the master schema cares about. Used to star interesting fields in a
# discovery report. This is field-NAME recognition, distinct from the value
# vocabulary in data/mappings.yml.
_TELEMETRY = {
    "fittier": "fit tier", "matchtier": "fit tier", "fitrating": "fit tier",
    "systemfittier": "fit tier",
    "matchscorepercent": "match score", "matchscore": "match score",
    "matchpct": "match score", "automatedmatchscore": "match score",
    "dispositionreason": "disposition", "rejectionreason": "disposition",
    "disposition": "disposition", "finaldisposition": "disposition",
    "stagereached": "stage", "currentstage": "stage", "laststage": "stage",
    "furtheststage": "stage",
    "parsedskills": "parsed skills", "parsedkeywordsmatched": "parsed skills",
    "skillsparsed": "parsed skills", "parsedcompetencies": "parsed skills",
    "autoadvanced": "auto-screen flag", "autoscreened": "auto-screen flag",
    "automationscreenapplied": "auto-screen flag",
}


def concept_for(field_name: str) -> str | None:
    """Return the master-schema concept a raw field name maps to, if any."""
    key = "".join(c for c in field_name.lower() if c.isalnum())
    return _TELEMETRY.get(key)


def _typename(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__


def infer_json(obj: Any) -> dict[str, dict]:
    """Walk a JSON value and return {path: {types, example, concept}}.

    Array elements collapse under a ``[]`` path segment so repeated records report
    one merged schema rather than N near-identical ones.
    """
    acc: dict[str, dict] = {}

    def visit(node: Any, path: str) -> None:
        t = _typename(node)
        if path:
            entry = acc.setdefault(path, {"types": set(), "example": None, "concept": None})
            entry["types"].add(t)
            if entry["example"] is None and t not in ("object", "array", "null"):
                entry["example"] = node
            leaf = path.split(".")[-1].replace("[]", "")
            entry["concept"] = entry["concept"] or concept_for(leaf)
        if isinstance(node, dict):
            for k, v in node.items():
                visit(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for item in node:
                visit(item, f"{path}[]")

    visit(obj, "")
    return acc


def _guess_scalar(text: str) -> str:
    if text == "":
        return "empty"
    low = text.lower()
    if low in ("true", "false", "yes", "no"):
        return "bool"
    try:
        int(text)
        return "int"
    except ValueError:
        pass
    try:
        float(text)
        return "float"
    except ValueError:
        pass
    if len(text) >= 8 and text[:4].isdigit() and text[4] in "-/":
        return "date?"
    return "string"


def infer_csv(path: str) -> dict[str, dict]:
    """Return {column: {types, example, concept}} for a CSV file."""
    acc: dict[str, dict] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            for col, val in row.items():
                entry = acc.setdefault(col, {"types": set(), "example": None, "concept": None})
                entry["types"].add(_guess_scalar((val or "").strip()))
                if entry["example"] is None and val:
                    entry["example"] = val
                entry["concept"] = entry["concept"] or concept_for(col)
    return acc


def format_report(schema: dict[str, dict], title: str) -> str:
    """Render an inferred schema as a readable text block (★ = known telemetry)."""
    lines = [f"# Schema: {title}", ""]
    width = max((len(p) for p in schema), default=10)
    for path in sorted(schema):
        info = schema[path]
        types = ",".join(sorted(info["types"]))
        star = "★" if info["concept"] else " "
        ex = info["example"]
        ex = (ex[:47] + "...") if isinstance(ex, str) and len(ex) > 50 else ex
        note = f"  → {info['concept']}" if info["concept"] else ""
        lines.append(f"{star} {path:<{width}}  {types:<14} e.g. {ex!r}{note}")
    starred = [i["concept"] for i in schema.values() if i["concept"]]
    lines += ["", f"{len(starred)} telemetry field(s) recognized: {sorted(set(starred))}"]
    return "\n".join(lines)
