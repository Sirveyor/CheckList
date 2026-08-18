"""Generates sample PDFs for visual review of the checklist layout."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from job_checklist.checklists import by_key  # noqa: E402
from job_checklist.layout import render  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    checklists = by_key()

    cases = {
        "sample_small_dock": (["Dock_chklst"], "26-25250"),
        "sample_large_engineering": (["Eginieering_chklst"], "26-25251"),
        "sample_multi_typical": (
            ["General_chklst", "Topo_chklst", "Drainage_AB_chklst"],
            "26-25252",
        ),
        "sample_stress_all": (list(checklists.keys()), "26-25253"),
    }

    for name, (keys, job_number) in cases.items():
        selected = [checklists[k] for k in keys]
        out_path = OUT_DIR / f"{name}.pdf"
        overflow = render(out_path, job_number, selected, date="8-18-26")
        status = f"OVERFLOW ({len(overflow)} lines dropped)" if overflow else "fit OK"
        print(f"{name}: {len(selected)} checklist(s), {sum(len(c.items) for c in selected)} items -> {status}")


if __name__ == "__main__":
    main()
