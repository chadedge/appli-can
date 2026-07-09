"""Loader and normalization helpers driven by ``data/mappings.yml``.

These functions turn raw vendor strings/values into the canonical vocabulary and
normalized types the master schema expects. The vocabulary itself lives in the
YAML file so it can grow as new dumps arrive without touching this code.
"""

from __future__ import annotations

import functools
import pathlib
from datetime import date, datetime
from typing import Any, Optional

import yaml

DEFAULT_MAPPINGS = pathlib.Path(__file__).resolve().parent.parent / "data" / "mappings.yml"


@functools.lru_cache(maxsize=None)
def load(path: str | pathlib.Path | None = None) -> dict[str, Any]:
    """Load and cache the mappings file."""
    with open(pathlib.Path(path) if path else DEFAULT_MAPPINGS) as fh:
        return yaml.safe_load(fh)


def stage_order() -> dict[str, int]:
    """Canonical stage -> order index, for 'how far did I get' comparisons."""
    return {s["value"]: s["order"] for s in load()["stages"]}


def map_stage(raw: Optional[str]) -> Optional[str]:
    """Map a raw vendor stage string to a canonical stage (or None if unknown)."""
    if not raw:
        return None
    return load()["stage_aliases"].get(raw.strip().lower())


def map_outcome(raw: Optional[str], stage: Optional[str] = None) -> str:
    """Map a raw disposition/status to a canonical outcome.

    ``stage`` (already-canonical) refines a generic rejection into
    rejected_after_interview vs rejected_after_review.
    """
    m = load()
    if not raw:
        return "unknown"
    text = raw.strip().lower()

    if text in {s.lower() for s in m.get("active_statuses", [])}:
        return "active"

    for rule in m["outcome_rules"]:
        if any(kw in text for kw in rule["any"]):
            outcome = rule["outcome"]
            if outcome == "rejected":
                interview_order = stage_order()["interview"]
                reached = stage_order().get(stage or "", -1)
                return (
                    "rejected_after_interview"
                    if reached >= interview_order
                    else "rejected_after_review"
                )
            return outcome
    return "unknown"


def fit_quality(raw_tier: Optional[str]) -> Optional[float]:
    """Map a raw vendor tier (A, Gold, ...) to a 0.0-1.0 quality, or None."""
    if not raw_tier:
        return None
    return load()["fit_tier_quality"].get(str(raw_tier).strip().lower())


def normalize_score(raw: Any) -> Optional[float]:
    """Normalize a match score to 0-100.

    Handles 0-1 floats (0.63 -> 63), 'N / 100' and 'N/100' strings, '68%',
    and plain 0-100 numbers. Returns None if it can't make sense of the value.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip().rstrip("%")
        if "/" in text:  # e.g. "59 / 100"
            num = text.split("/", 1)[0].strip()
            try:
                return float(num)
            except ValueError:
                return None
        try:
            raw = float(text)
        except ValueError:
            return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if 0 <= val <= 1:  # fractional scale
        return round(val * 100, 2)
    return val


def parse_date(raw: Any) -> Optional[date]:
    """Parse an ISO-ish date/datetime string to a date. None if unparseable."""
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if not text or text.lower() == "unknown":
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None
