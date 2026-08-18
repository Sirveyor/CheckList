"""Loading and parsing of the *_chklst.md checklist source files."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# When frozen by PyInstaller, bundled data lives under sys._MEIPASS rather
# than alongside this file on disk.
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = _BASE_DIR / "DOCUMENTS"

# U+2010/2011/2012 ("hyphen", "non-breaking hyphen", "figure dash") have no
# equivalent in the WinAnsi encoding the PDF's base-14 fonts use, and render
# as a missing-glyph box. Normalize them to a plain ASCII hyphen; en/em dash,
# curly quotes, and the ellipsis are all present in WinAnsi and render fine.
_DASH_FIXUP = str.maketrans({"‐": "-", "‑": "-", "‒": "-"})


@dataclass(frozen=True)
class Checklist:
    key: str
    title: str
    items: tuple[str, ...]


def _parse_file(path: Path) -> Checklist:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    lines = [line for line in lines if line]
    title = lines[0].translate(_DASH_FIXUP)
    # Split on "☐" rather than just stripping a leading one: at least one
    # source file has two items run together on the same line with no
    # newline between them, and this handles that case along with the
    # normal one-checkbox-per-line files.
    items = tuple(
        chunk.strip().translate(_DASH_FIXUP)
        for line in lines[1:]
        for chunk in line.split("☐")
        if chunk.strip()
    )
    return Checklist(key=path.stem, title=title, items=items)


def load_all(documents_dir: Path = DOCUMENTS_DIR) -> list[Checklist]:
    paths = sorted(documents_dir.glob("*_chklst.md"))
    return [_parse_file(p) for p in paths]


def by_key(documents_dir: Path = DOCUMENTS_DIR) -> dict[str, Checklist]:
    return {c.key: c for c in load_all(documents_dir)}
