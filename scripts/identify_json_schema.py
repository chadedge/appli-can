"""
A script to identify the JSON schema of a given JSON file.
This script is helpful in identifying fields and their types in a JSON file,
so that a common structure may be built between different Applicant Tracking Systems (ATS).

Also handles .csv dumps. Fields that match known screening telemetry (fit tiers,
match scores, dispositions, ...) are starred (★) so you can spot the valuable
data quickly.

Usage:
    python scripts/identify_json_schema.py FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from applican import infer  # noqa: E402


def describe(path: pathlib.Path) -> str:
    if path.suffix.lower() == ".csv":
        return infer.format_report(infer.infer_csv(str(path)), path.name)
    if path.suffix.lower() == ".json":
        return infer.format_report(infer.infer_json(json.loads(path.read_text())), path.name)
    raise ValueError(f"unsupported file type: {path.suffix} (expected .json or .csv)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover fields & types in a JSON/CSV dump.")
    ap.add_argument("files", nargs="+", type=pathlib.Path)
    args = ap.parse_args()

    rc = 0
    for f in args.files:
        if not f.is_file():
            print(f"error: {f} not found", file=sys.stderr)
            rc = 1
            continue
        try:
            print(describe(f))
            print()
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"error reading {f}: {exc}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
