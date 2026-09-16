"""Tkinter GUI: pick a job number and checklists, generate the PDF into the
job folder on the network share, log it, and optionally send it to the
chosen printer.
"""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from . import jobfolder, layout, printing, review, theme
from .checklists import Checklist, Item, dedupe, load_all


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Time Sheet and Check List")
        self.geometry("560x720")

        self.checklists: list[Checklist] = load_all()
        self.checklist_vars: dict[str, tk.BooleanVar] = {}

        self.style = ttk.Style(self)
        self.dark_mode_var = tk.BooleanVar(value=False)

        self._build_job_row()
        self._build_checklist_area()
        self._build_custom_area()
        self._build_printer_row()
        self._build_action_row()

        self._apply_theme()

    # ---- UI construction ----

    def _build_job_row(self) -> None:
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="x")

        ttk.Label(frame, text="Job Number").grid(row=0, column=0, sticky="w")
        self.job_number_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.job_number_var, width=16).grid(row=0, column=1, sticky="w", padx=(6, 12))

        ttk.Label(frame, text="Ext").grid(row=0, column=2, sticky="w")
        self.extension_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.extension_var, width=6).grid(row=0, column=3, sticky="w", padx=(6, 20))

        ttk.Label(frame, text="Date").grid(row=0, column=4, sticky="w")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%m-%d-%y"))
        ttk.Entry(frame, textvariable=self.date_var, width=12).grid(row=0, column=5, sticky="w", padx=(6, 20))

        ttk.Checkbutton(
            frame, text="Dark Mode", variable=self.dark_mode_var, command=self._apply_theme
        ).grid(row=0, column=6, sticky="e")
        frame.columnconfigure(6, weight=1)

    def _build_checklist_area(self) -> None:
        outer = ttk.LabelFrame(self, text="Checklists", padding=10)
        outer.pack(fill="both", expand=True, padx=10, pady=5)

        self.checklist_canvas = canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for cl in self.checklists:
            var = tk.BooleanVar(value=False)
            self.checklist_vars[cl.key] = var
            ttk.Checkbutton(inner, text=f"{cl.title} ({len(cl.items)} items)", variable=var).pack(anchor="w")

    def _build_custom_area(self) -> None:
        outer = ttk.LabelFrame(self, text="Custom / Job-Specific Items", padding=10)
        outer.pack(fill="x", padx=10, pady=(0, 5))
        outer.columnconfigure(1, weight=1)

        ttk.Label(outer, text="Heading").grid(row=0, column=0, sticky="w")
        self.custom_title_var = tk.StringVar(value="Job-Specific Items")
        ttk.Entry(outer, textvariable=self.custom_title_var).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Label(outer, text="One item per line:").grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 2))
        self.custom_items_text = tk.Text(outer, height=4, wrap="word", borderwidth=1, relief="solid")
        self.custom_items_text.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _build_printer_row(self) -> None:
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="x")

        self.print_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Print", variable=self.print_var, command=self._update_printer_state
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(frame, text="Printer").grid(row=0, column=1, sticky="w", padx=(12, 0))
        try:
            printers = printing.list_printers()
        except Exception:
            printers = []
        default = printing.default_printer()
        if default not in printers:
            default = printers[0] if printers else None

        self.printer_var = tk.StringVar(value=default or "")
        self.printer_combo = ttk.Combobox(
            frame, textvariable=self.printer_var, values=printers, width=40, state="readonly"
        )
        self.printer_combo.grid(row=0, column=2, sticky="w", padx=(6, 0))
        self._update_printer_state()

    def _update_printer_state(self) -> None:
        self.printer_combo.configure(state="readonly" if self.print_var.get() else "disabled")

    def _build_action_row(self) -> None:
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="x")

        self.status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.status_var, foreground="gray").pack(side="left")

        ttk.Button(frame, text="Generate", command=self.on_generate).pack(side="right")

    def _apply_theme(self) -> None:
        name = "dark" if self.dark_mode_var.get() else "light"
        palette = theme.apply_theme(self, self.style, name)
        self.configure(bg=palette["bg"])
        self.checklist_canvas.configure(bg=palette["bg"])
        self.custom_items_text.configure(
            bg=palette["entry_bg"], fg=palette["entry_fg"], insertbackground=palette["fg"]
        )

    # ---- Actions ----

    def selected_checklists(self) -> list[Checklist]:
        return [cl for cl in self.checklists if self.checklist_vars[cl.key].get()]

    def custom_checklist(self) -> Checklist | None:
        raw = self.custom_items_text.get("1.0", "end")
        items = tuple(Item(text=line.strip()) for line in raw.splitlines() if line.strip())
        if not items:
            return None
        title = self.custom_title_var.get().strip() or "Job-Specific Items"
        return Checklist(key="__custom__", title=title, items=items)

    def on_generate(self) -> None:
        job_number = self.job_number_var.get().strip()
        date = self.date_var.get().strip()
        printer_name = self.printer_var.get()

        try:
            jobfolder.parse_job_number(job_number)
        except ValueError as e:
            messagebox.showerror("Invalid job number", str(e))
            return

        selected = self.selected_checklists()
        custom = self.custom_checklist()
        if custom:
            selected = [custom] + selected
        selected = dedupe(selected)

        selected = review.review_items(self, selected)
        if selected is None:
            return

        extension = self.extension_var.get().strip()
        display_job_number = f"{job_number}-{extension}" if extension else job_number

        try:
            folder = jobfolder.ensure_job_folder(job_number)
        except OSError as e:
            messagebox.showerror("Could not create job folder", f"{e}\n\nIs the J: drive connected?")
            return

        out_path = folder / f"{display_job_number} Checklist.pdf"
        overflow = layout.render(out_path, display_job_number, selected, date=date)

        jobfolder.log_job(display_job_number)

        if self.print_var.get() and printer_name:
            try:
                printing.print_pdf(out_path, printer_name)
            except Exception as e:
                messagebox.showwarning(
                    "Saved, but printing failed",
                    f"The PDF was saved to:\n{out_path}\n\nbut sending it to {printer_name!r} failed:\n{e}",
                )
                return

        msg = f"Saved to:\n{out_path}"
        if overflow:
            msg += f"\n\n{len(overflow)} checklist line(s) did not fit on the page and were left off."
        self.status_var.set("Done.")
        messagebox.showinfo("Checklist generated", msg)


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
