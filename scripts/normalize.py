"""
Normalize raw ATS dumps into the Appli-CAN! master schema.

Walks an input directory (one child folder/file per company), detects each
vendor, maps every dump onto the common schema, and writes a single validated
JSON dataset to the reports folder.

Usage:
    python scripts/normalize.py [--input DIR] [--out FILE]

Defaults: --input input  --out reports/normalized.json
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from applican import normalize  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize ATS dumps into the master schema.")
    ap.add_argument("--input", type=pathlib.Path, default=pathlib.Path("input"),
                    help="directory of company dumps (default: input)")
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("reports/normalized.json"),
                    help="output JSON file (default: reports/normalized.json)")
    args = ap.parse_args()

    if not args.input.is_dir():
        print(f"error: {args.input} is not a directory", file=sys.stderr)
        return 1

    dataset, warnings = normalize.normalize_dataset(args.input)
    for w in warnings:
        print(f"  ! {w}", file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dataset.model_dump_json(indent=2))

    print(f"Normalized {len(dataset.applications)} application(s) from "
          f"{len(dataset.sources)} source(s) -> {args.out}")
    for src in dataset.sources:
        n = sum(1 for a in dataset.applications if a.company == src.company)
        print(f"  • {src.company} ({src.ats_vendor}): {n} application(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
