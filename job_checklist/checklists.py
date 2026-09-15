"""Loading and parsing of the *_chklst.md checklist source files."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

# When frozen by PyInstaller, bundled data lives under sys._MEIPASS rather
# than alongside this file on disk.
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = _BASE_DIR / "DOCUMENTS"
CORE_ITEMS_FILE = "Core_items.md"

# U+2010/2011/2012 ("hyphen", "non-breaking hyphen", "figure dash") have no
# equivalent in the WinAnsi encoding the PDF's base-14 fonts use, and render
# as a missing-glyph box. Normalize them to a plain ASCII hyphen; en/em dash,
# curly quotes, and the ellipsis are all present in WinAnsi and render fine.
_DASH_FIXUP = str.maketrans({"‐": "-", "‑": "-", "‒": "-"})


class Item(NamedTuple):
    text: str
    # Set only for items sourced from the shared item library (Core_items.md).
    # Lets dedupe() collapse the same library item pulled in by multiple
    # selected checklists, without relying on fragile text matching.
    id: str | None = None


@dataclass(frozen=True)
class Checklist:
    key: str
    title: str
    items: tuple[Item, ...]


def _load_library(documents_dir: Path) -> dict[str, str]:
    path = documents_dir / CORE_ITEMS_FILE
    if not path.exists():
        return {}
    library: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("[") or "]" not in line:
            continue
        item_id, _, text = line[1:].partition("]")
        library[item_id.strip()] = text.strip().translate(_DASH_FIXUP)
    return library


def _parse_file(path: Path, library: dict[str, str]) -> Checklist:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    lines = [line for line in lines if line]
    title = lines[0].translate(_DASH_FIXUP)

    items: list[Item] = []
    for line in lines[1:]:
        if line.startswith("@"):
            item_id = line[1:].strip()
            items.append(Item(text=library[item_id], id=item_id))
            continue
        # Split on "☐" rather than just stripping a leading one: at least one
        # source file has two items run together on the same line with no
        # newline between them, and this handles that case along with the
        # normal one-checkbox-per-line files.
        for chunk in line.split("☐"):
            chunk = chunk.strip()
            if chunk:
                items.append(Item(text=chunk.translate(_DASH_FIXUP)))
    return Checklist(key=path.stem, title=title, items=tuple(items))


def load_all(documents_dir: Path = DOCUMENTS_DIR) -> list[Checklist]:
    library = _load_library(documents_dir)
    paths = sorted(documents_dir.glob("*_chklst.md"))
    return [_parse_file(p, library) for p in paths]


def by_key(documents_dir: Path = DOCUMENTS_DIR) -> dict[str, Checklist]:
    return {c.key: c for c in load_all(documents_dir)}


def dedupe(checklists: list[Checklist]) -> list[Checklist]:
    """Drop items already contributed by an earlier checklist in the list.

    Only items sourced from the shared item library (those with an id) are
    deduplicated; free-typed items are always kept.
    """
    seen: set[str] = set()
    result = []
    for cl in checklists:
        kept = []
        for item in cl.items:
            if item.id is not None:
                if item.id in seen:
                    continue
                seen.add(item.id)
            kept.append(item)
        result.append(Checklist(key=cl.key, title=cl.title, items=tuple(kept)))
    return result
