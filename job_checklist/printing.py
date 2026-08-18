"""Printer enumeration and silent printing of a generated PDF.

Printing is delegated to whatever PDF handler is registered for .pdf on the
workstation (Adobe Acrobat/Reader, Foxit, etc.) via the Windows shell's
"printto" verb, which sends the job to a specific printer without opening a
dialog or changing the system default printer.
"""
from __future__ import annotations

from pathlib import Path

import win32api
import win32print


# Driver-name substrings (case-insensitive) for "printers" that don't
# produce paper -- these show up alongside real printers in Windows but
# should not appear in the picker.
_VIRTUAL_DRIVER_KEYWORDS = (
    "xps document writer",
    "print to pdf",
    "pdf converter",
    "pdf writer",
    "shared fax driver",
    "send to microsoft onenote",
)


def list_printers() -> list[str]:
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags, None, 2)
    return [
        p["pPrinterName"]
        for p in printers
        if not any(kw in p["pDriverName"].lower() for kw in _VIRTUAL_DRIVER_KEYWORDS)
    ]


def default_printer() -> str | None:
    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return None


def print_pdf(path: Path, printer_name: str) -> None:
    win32api.ShellExecute(0, "printto", str(path), f'"{printer_name}"', ".", 0)
