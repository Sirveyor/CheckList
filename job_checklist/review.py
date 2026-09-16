"""Final review dialog shown before a checklist PDF is generated.

Lets the user drop individual items from the set about to be printed
(job-local only -- never touches the source *_chklst.md files), and
save/load that final item set as a named, reusable combo via `selections`.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from . import selections, theme
from .checklists import Checklist, Item

_Group = dict  # {"key": str, "title": str, "items": list[Item]}


def review_items(parent: tk.Tk, checklists: list[Checklist]) -> list[Checklist] | None:
    """Shows the review dialog. Returns the final list[Checklist] to print,
    or None if the user cancelled.
    """
    groups: list[_Group] = [
        {"key": cl.key, "title": cl.title, "items": list(cl.items)} for cl in checklists
    ]
    result: list[list[Checklist]] = [None]  # boxed, so callbacks can set it

    dialog = tk.Toplevel(parent)
    dialog.title("Review Checklist Items")
    dialog.geometry("560x600")
    dialog.transient(parent)

    palette = theme.PALETTES["dark" if getattr(parent, "dark_mode_var", None) and parent.dark_mode_var.get() else "light"]
    dialog.configure(bg=palette["bg"])

    outer = ttk.Frame(dialog, padding=10)
    outer.pack(fill="both", expand=True)

    list_frame = ttk.Frame(outer)
    list_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(list_frame, borderwidth=0, highlightthickness=0, bg=palette["bg"])
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def remove_item(group: _Group, item: Item) -> None:
        group["items"].remove(item)
        render()

    def render() -> None:
        for child in inner.winfo_children():
            child.destroy()
        any_items = False
        for group in groups:
            if not group["items"]:
                continue
            any_items = True
            ttk.Label(inner, text=group["title"], font=("", 10, "bold")).pack(anchor="w", pady=(8, 2))
            for item in group["items"]:
                row = ttk.Frame(inner)
                row.pack(fill="x", anchor="w")
                ttk.Button(
                    row, text="✕", width=3, command=lambda g=group, i=item: remove_item(g, i)
                ).pack(side="left")
                ttk.Label(row, text=item.text, wraplength=380, justify="left").pack(
                    side="left", padx=(6, 0), anchor="w"
                )
        if not any_items:
            ttk.Label(inner, text="No items selected.").pack(anchor="w", pady=8)
        canvas.configure(scrollregion=canvas.bbox("all"))

    def current_checklists() -> list[Checklist]:
        return [
            Checklist(key=g["key"], title=g["title"], items=tuple(g["items"]))
            for g in groups
            if g["items"]
        ]

    def on_save() -> None:
        current = current_checklists()
        if not current:
            messagebox.showwarning("Nothing to save", "There are no items left to save.", parent=dialog)
            return
        name = simpledialog.askstring("Save Combo", "Name for this combo:", parent=dialog)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        existing = selections.load_all()
        if name in existing and not messagebox.askyesno(
            "Overwrite?", f'A saved combo named "{name}" already exists. Overwrite it?', parent=dialog
        ):
            return
        try:
            selections.save(name, current)
        except OSError as e:
            messagebox.showerror(
                "Could not save combo", f"{e}\n\nIs the J: drive connected?", parent=dialog
            )
            return
        messagebox.showinfo("Saved", f'Combo "{name}" saved.', parent=dialog)

    def on_load() -> None:
        saved = selections.load_all()
        if not saved:
            messagebox.showinfo("No saved combos", "There are no saved combos yet.", parent=dialog)
            return
        name = _pick_saved_name(dialog, sorted(saved))
        if name is None:
            return
        groups.clear()
        groups.extend(
            {"key": cl.key, "title": cl.title, "items": list(cl.items)} for cl in saved[name]
        )
        render()

    def on_confirm() -> None:
        result[0] = current_checklists()
        dialog.destroy()

    def on_cancel() -> None:
        result[0] = None
        dialog.destroy()

    button_row = ttk.Frame(outer, padding=(0, 10, 0, 0))
    button_row.pack(fill="x")
    ttk.Button(button_row, text="Save…", command=on_save).pack(side="left")
    ttk.Button(button_row, text="Load…", command=on_load).pack(side="left", padx=(6, 0))
    ttk.Button(button_row, text="Cancel", command=on_cancel).pack(side="right")
    ttk.Button(button_row, text="Confirm && Generate", command=on_confirm).pack(side="right", padx=(0, 6))

    render()

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.grab_set()
    parent.wait_window(dialog)
    return result[0]


def _pick_saved_name(parent: tk.Toplevel, names: list[str]) -> str | None:
    """Small modal listbox picker. Returns the chosen name, or None if cancelled."""
    picker = tk.Toplevel(parent)
    picker.title("Load Combo")
    picker.transient(parent)

    choice: list[str] = [None]

    ttk.Label(picker, text="Choose a saved combo:", padding=(10, 10, 10, 0)).pack(anchor="w")
    listbox = tk.Listbox(picker, height=min(10, len(names)), exportselection=False)
    for name in names:
        listbox.insert("end", name)
    listbox.selection_set(0)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    def confirm(_event=None) -> None:
        selection = listbox.curselection()
        if selection:
            choice[0] = names[selection[0]]
        picker.destroy()

    def cancel() -> None:
        picker.destroy()

    listbox.bind("<Double-Button-1>", confirm)

    row = ttk.Frame(picker, padding=(10, 0, 10, 10))
    row.pack(fill="x")
    ttk.Button(row, text="Cancel", command=cancel).pack(side="right")
    ttk.Button(row, text="Load", command=confirm).pack(side="right", padx=(0, 6))

    picker.protocol("WM_DELETE_WINDOW", cancel)
    picker.grab_set()
    parent.wait_window(picker)
    return choice[0]
