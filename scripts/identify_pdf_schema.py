"""
A script to identify the contents and formatting of a given PDF file.
This script is helpful in identifying fields and their types in a PDF,
so that a common structure may be built between different Applicant Tracking Systems (ATS).

Works on .pdf (needs `pypdf`) and on already-flattened .txt exports. It prints the
key/value blocks it reconstructs, so you can see how a prose/PDF dump maps onto the
common schema.

Usage:
    python scripts/identify_pdf_schema.py FILE
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from applican import infer, textparse  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract & structure a PDF/flattened-text dump.")
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--show-text", action="store_true", help="also print the raw extracted text")
    args = ap.parse_args()

    if not args.file.is_file():
        print(f"error: {args.file} not found", file=sys.stderr)
        return 1

    try:
        text = textparse.extract_text(args.file)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.show_text:
        print("=== extracted text ===")
        print(text)
        print("=== end text ===\n")

    blocks = textparse.parse_blocks(text)
    print(f"# {args.file.name}: {len(blocks)} block(s)\n")
    for i, block in enumerate(blocks, 1):
        kv = block["kv"]
        if not kv:
            print(f"[block {i}] (no key/value pairs — prose/notice)")
            continue
        print(f"[block {i}]")
        for key, value in kv.items():
            concept = infer.concept_for(key)
            star = "★" if concept else " "
            tag = f"  → {concept}" if concept else ""
            print(f" {star} {key}: {value}{tag}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
