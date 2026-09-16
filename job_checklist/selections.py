"""Saving and loading named, reusable combinations of checklist items.

Saved combos are written to the shared job-folder drive (same convention as
jobfolder.LOG_PATH) so every workstation can save and reload the same set of
combos, independent of which checklists happen to be checked on this job.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import jobfolder
from .checklists import Checklist, Item

SAVE_PATH = jobfolder.SHARE_ROOT / "job_checklist_selections.json"


def load_all(path: Path = SAVE_PATH) -> dict[str, list[Checklist]]:
    """Returns every saved combo, keyed by name. Empty dict if none exist yet."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, list[Checklist]] = {}
    for name, checklists in raw.items():
        result[name] = [
            Checklist(
                key=cl["key"],
                title=cl["title"],
                items=tuple(Item(text=item["text"], id=item.get("id")) for item in cl["items"]),
            )
            for cl in checklists
        ]
    return result


def save(name: str, checklists: list[Checklist], path: Path = SAVE_PATH) -> None:
    """Writes (or overwrites) a named combo. Stores full item text/ids so a
    reload doesn't depend on the source *_chklst.md files being unchanged.
    """
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    data[name] = [
        {
            "key": cl.key,
            "title": cl.title,
            "items": [{"text": item.text, "id": item.id} for item in cl.items],
        }
        for cl in checklists
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
