"""
A script to extract compressed files from a given directory.
This script is helpful in extracting compressed files from a directory,
so that the contents can be analyzed.

Usage:
    python scripts/extract_compressed_files.py [DIR]

DIR defaults to ./input. Each archive is extracted into a sibling folder named
after the archive (e.g. acme_dump.zip -> input/acme_dump/), which matches the
"one folder per company" convention the pipeline expects.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".bz2"}


def extract_all(directory: pathlib.Path) -> list[pathlib.Path]:
    """Extract every supported archive in ``directory``. Returns the output dirs."""
    extracted: list[pathlib.Path] = []
    for archive in sorted(directory.iterdir()):
        if not archive.is_file():
            continue
        # ".tar.gz"/".tgz" both count; check the full suffix chain.
        suffixes = set(archive.suffixes[-2:]) | {archive.suffix}
        if not (suffixes & ARCHIVE_SUFFIXES):
            continue
        dest = directory / archive.name.split(".")[0]
        dest.mkdir(exist_ok=True)
        try:
            shutil.unpack_archive(str(archive), str(dest))
        except (shutil.ReadError, ValueError) as exc:
            print(f"  ! could not extract {archive.name}: {exc}", file=sys.stderr)
            continue
        print(f"  extracted {archive.name} -> {dest.relative_to(directory.parent)}/")
        extracted.append(dest)
    return extracted


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("directory", nargs="?", default="input", type=pathlib.Path,
                    help="directory to scan for archives (default: input)")
    args = ap.parse_args()

    if not args.directory.is_dir():
        print(f"error: {args.directory} is not a directory", file=sys.stderr)
        return 1

    results = extract_all(args.directory)
    print(f"\n{len(results)} archive(s) extracted." if results
          else "No supported archives found (nothing to do).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
