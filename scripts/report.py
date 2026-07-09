"""
Build the Appli-CAN! funnel report from normalized data.

Reads a normalized dataset (default reports/normalized.json, produced by
normalize.py) and writes a per-company Markdown report highlighting funnels,
scores, and automation-driven rejections.

Usage:
    python scripts/report.py [--data FILE] [--out FILE]

Defaults: --data reports/normalized.json  --out reports/funnel_report.md
"""

from __future__ import annotations

import argparse
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from applican import report  # noqa: E402
from applican.schema import Dataset  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the funnel report from normalized data.")
    ap.add_argument("--data", type=pathlib.Path, default=pathlib.Path("reports/normalized.json"))
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("reports/funnel_report.md"))
    args = ap.parse_args()

    if not args.data.is_file():
        print(f"error: {args.data} not found — run scripts/normalize.py first.", file=sys.stderr)
        return 1

    dataset = Dataset.model_validate_json(args.data.read_text())
    today = datetime.date.today().isoformat()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report.build_markdown(dataset, generated=today))

    print(report.build_terminal(dataset))
    print(f"\nFull report -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
