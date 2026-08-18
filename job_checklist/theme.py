"""Light/dark color palettes for the ttk UI."""
from __future__ import annotations

from tkinter import ttk

PALETTES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "select_bg": "#0078d7",
        "select_fg": "#ffffff",
        "button_bg": "#e1e1e1",
        "border": "#a0a0a0",
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#e0e0e0",
        "entry_bg": "#2d2d2d",
        "entry_fg": "#e0e0e0",
        "select_bg": "#0a84ff",
        "select_fg": "#ffffff",
        "button_bg": "#3c3c3c",
        "border": "#555555",
    },
}


def apply_theme(root: ttk.Widget, style: ttk.Style, name: str) -> dict[str, str]:
    """Applies the named palette ("light" or "dark") to every ttk widget via
    the shared "T*" style names, so existing widgets pick it up without
    needing to be individually reconfigured. Returns the palette used, so
    callers can apply it to any plain tk widgets (Canvas, Tk root) too.
    """
    p = PALETTES[name]
    style.theme_use("clam")

    style.configure(".", background=p["bg"], foreground=p["fg"])
    style.configure("TFrame", background=p["bg"])
    style.configure("TLabel", background=p["bg"], foreground=p["fg"])
    style.configure("TLabelframe", background=p["bg"], foreground=p["fg"], bordercolor=p["border"])
    style.configure("TLabelframe.Label", background=p["bg"], foreground=p["fg"])

    style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"])
    style.map(
        "TCheckbutton",
        background=[("active", p["bg"])],
        foreground=[("active", p["fg"])],
        indicatorcolor=[("selected", p["select_bg"]), ("!selected", p["entry_bg"])],
    )

    style.configure("TButton", background=p["button_bg"], foreground=p["fg"], bordercolor=p["border"])
    style.map("TButton", background=[("active", p["select_bg"])], foreground=[("active", p["select_fg"])])

    style.configure("TEntry", fieldbackground=p["entry_bg"], foreground=p["entry_fg"], insertcolor=p["fg"], bordercolor=p["border"])
    style.map("TEntry", fieldbackground=[("readonly", p["entry_bg"])])

    style.configure("TCombobox", fieldbackground=p["entry_bg"], foreground=p["entry_fg"], background=p["button_bg"], arrowcolor=p["fg"], bordercolor=p["border"])
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", p["entry_bg"])],
        foreground=[("readonly", p["entry_fg"])],
        selectbackground=[("readonly", p["entry_bg"])],
        selectforeground=[("readonly", p["entry_fg"])],
    )

    style.configure("Vertical.TScrollbar", background=p["button_bg"], troughcolor=p["bg"], arrowcolor=p["fg"], bordercolor=p["border"])

    root.option_add("*TCombobox*Listbox.background", p["entry_bg"])
    root.option_add("*TCombobox*Listbox.foreground", p["entry_fg"])
    root.option_add("*TCombobox*Listbox.selectBackground", p["select_bg"])
    root.option_add("*TCombobox*Listbox.selectForeground", p["select_fg"])

    return p
