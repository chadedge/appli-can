"""Text extraction and key/value block parsing for the 'flattened PDF' worst case.

Some companies fulfill a request by exporting a PDF and calling it a day. Once
flattened to text it's a loose set of ``Key: Value`` lines grouped into record
blocks. This module pulls the text out (PDF or plain .txt) and reconstructs those
blocks into dicts the normalizer can consume.
"""

from __future__ import annotations

import pathlib
import re

_MARKER = re.compile(r"^\s*-{2,}.*-{2,}\s*$")  # e.g. "--- APPLICATION RECORD ---"


def extract_text(path: str | pathlib.Path) -> str:
    """Return the text of a .txt or .pdf file.

    PDF support is best-effort: uses pypdf or PyPDF2 if installed, otherwise
    raises a clear error so the caller can tell the user what to install.
    """
    p = pathlib.Path(path)
    if p.suffix.lower() != ".pdf":
        return p.read_text()
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError as exc:  # pragma: no cover - env dependent
            raise RuntimeError(
                "Reading PDFs needs 'pypdf' (pip install pypdf). "
                "If your dump is JSON/CSV, use identify_json_schema.py instead."
            ) from exc
    reader = PdfReader(str(p))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_blocks(text: str) -> list[dict]:
    """Split text into blank-line-separated blocks of parsed key/value pairs.

    Each block is ``{"kv": {key: value}, "raw": "<block text>"}``. Marker lines
    like ``--- NOTICE ---`` are stripped from kv but kept in ``raw`` so callers can
    still detect section semantics (e.g. a withholding notice).
    """
    blocks: list[dict] = []
    for chunk in re.split(r"\n\s*\n", text.strip()):
        if not chunk.strip():
            continue
        kv: dict[str, str] = {}
        for line in chunk.splitlines():
            if _MARKER.match(line) or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if key and value:
                kv[key] = value
        blocks.append({"kv": kv, "raw": chunk.strip()})
    return blocks
