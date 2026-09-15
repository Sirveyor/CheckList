"""Renders the one-page Time Sheet and Check List PDF.

The header, results, and footer sections are fixed-position. Whatever
vertical space is left between them is handed to the checklist area,
which auto-selects a column count and font size so the selected
checklists' items fit on the single page.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from .checklists import Checklist

PAGE_W, PAGE_H = letter

MARGIN_X = 30
TOP_Y = PAGE_H - 16
BOTTOM_Y = 18

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# Column/font sizes tried, largest first, when fitting the checklist area.
FONT_CANDIDATES = [9, 8.5, 8, 7.5, 7, 6.5, 6]
COLUMN_CANDIDATES = [2, 3, 4]


def checkbox(c: Canvas, x: float, y: float, size: float) -> None:
    c.rect(x, y, size, size)


def blank_line(c: Canvas, x1: float, x2: float, y: float) -> None:
    c.line(x1, y, x2, y)


def _row(c: Canvas, x: float, y: float, parts, font: str = FONT, size: float = 9, gap: float = 6, cb: float = 8) -> float:
    """Draws a left-to-right row of parts, each sized by measured text width
    so labels/checkboxes/blanks never overlap. Returns the ending x.

    Part kinds:
      ("text", s[, font, size])
      ("checkbox_label", s)   -- a checkbox followed by its label
      ("blank", width)        -- a blank line of the given width
      ("blank_to", target_x)  -- a blank line from the current x to target_x
    """
    cx = x
    for part in parts:
        kind = part[0]
        if kind == "text":
            s = part[1]
            fnt = part[2] if len(part) > 2 else font
            sz = part[3] if len(part) > 3 else size
            c.setFont(fnt, sz)
            c.drawString(cx, y, s)
            cx += stringWidth(s, fnt, sz) + gap
        elif kind == "checkbox_label":
            s = part[1]
            checkbox(c, cx, y - 1, cb)
            cx += cb + 4
            c.setFont(font, size)
            c.drawString(cx, y, s)
            cx += stringWidth(s, font, size) + gap
        elif kind == "blank":
            w = part[1]
            blank_line(c, cx, cx + w, y - 1)
            cx += w + gap
        elif kind == "blank_to":
            target = part[1]
            blank_line(c, cx, target, y - 1)
            cx = target + gap
        else:
            raise ValueError(f"unknown row part kind: {kind!r}")
    return cx


@dataclass
class ChecklistLine:
    kind: str  # "heading" | "item" | "item_cont" | "spacer"
    text: str


def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if stringWidth(trial, font, size) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _build_lines(checklists: list[Checklist], font: str, size: float, text_width: float) -> list[ChecklistLine]:
    lines: list[ChecklistLine] = []
    for i, cl in enumerate(checklists):
        if i > 0:
            lines.append(ChecklistLine("spacer", ""))
        lines.append(ChecklistLine("heading", cl.title))
        for item in cl.items:
            wrapped = _wrap(item.text, font, size, text_width)
            lines.append(ChecklistLine("item", wrapped[0]))
            for cont in wrapped[1:]:
                lines.append(ChecklistLine("item_cont", cont))
    return lines


def _fit(checklists: list[Checklist], box_w: float, box_h: float):
    """Return (font_size, num_cols, line_height, lines, overflow_lines)."""
    col_gap = 14
    text_indent_ratio = 1.6  # multiples of font size, for hanging indent

    best = None
    for size in FONT_CANDIDATES:
        line_height = size * 1.35
        max_lines_per_col = max(1, int(box_h // line_height))
        for num_cols in COLUMN_CANDIDATES:
            col_width = (box_w - (num_cols - 1) * col_gap) / num_cols
            text_indent = size * text_indent_ratio
            text_width = col_width - text_indent
            if text_width <= 20:
                continue
            lines = _build_lines(checklists, FONT, size, text_width)
            capacity = max_lines_per_col * num_cols
            if len(lines) <= capacity:
                # Fits. Prefer largest font, then fewest columns.
                return size, num_cols, line_height, col_width, text_indent, lines, []
            if best is None:
                best = (size, num_cols, line_height, col_width, text_indent, lines, capacity)

    # Nothing fit: use the smallest font / most columns tried, and report overflow.
    size, num_cols, line_height, col_width, text_indent, lines, capacity = best
    return size, num_cols, line_height, col_width, text_indent, lines[:capacity], lines[capacity:]


def _draw_checklist_area(c: Canvas, checklists: list[Checklist], x: float, top: float, w: float, h: float) -> list[ChecklistLine]:
    if not checklists:
        c.setFont(FONT, 8)
        c.setFillGray(0.5)
        c.drawString(x, top - 10, "(no checklists selected)")
        c.setFillGray(0)
        return []

    size, num_cols, line_height, col_width, text_indent, lines, overflow = _fit(checklists, w, h)
    col_gap = 14

    lines_per_col = max(1, int(h // line_height))
    idx = 0
    for col in range(num_cols):
        col_x = x + col * (col_width + col_gap)
        y = top - size
        for _ in range(lines_per_col):
            if idx >= len(lines):
                break
            line = lines[idx]
            idx += 1
            if line.kind == "spacer":
                y -= line_height * 0.4
                continue
            if line.kind == "heading":
                c.setFont(FONT_BOLD, size)
                c.drawString(col_x, y, line.text)
            elif line.kind == "item":
                box_size = size * 0.75
                checkbox(c, col_x, y - box_size * 0.15, box_size)
                c.setFont(FONT, size)
                c.drawString(col_x + text_indent, y, line.text)
            else:  # item_cont
                c.setFont(FONT, size)
                c.drawString(col_x + text_indent, y, line.text)
            y -= line_height
        if idx >= len(lines):
            break

    return overflow


def render(
    out_path: Path,
    job_number: str,
    checklists: list[Checklist],
    date: str = "",
) -> list[ChecklistLine]:
    """Render the form to out_path. Returns any checklist lines that did not fit.

    Crew, times, and results are left blank for the field crew to fill in by
    hand; only the job number, selected checklists, and print date are known
    at generation time.
    """
    if not date:
        date = datetime.now().strftime("%m-%d-%y")
    c = Canvas(str(out_path), pagesize=letter)

    cb = 8
    usable_w = PAGE_W - 2 * MARGIN_X

    y = TOP_Y
    c.setFont(FONT_BOLD, 16)
    c.drawString(MARGIN_X, y - 14, "TIME SHEET AND CHECK LIST")
    c.setFont(FONT_BOLD, 14)
    c.drawRightString(PAGE_W - MARGIN_X, y - 14, f"Job# {job_number}")
    y -= 28

    _row(c, MARGIN_X, y, [("text", "Date"), ("blank", 100)])
    if date:
        c.setFont(FONT, 9)
        c.drawString(MARGIN_X + stringWidth("Date", FONT, 9) + 8, y + 1, date)
    y -= 16

    # Row: Crew / Date / Arrived / Departed / Total Time / Cost, sized to fit the page width.
    row_labels = ["Crew", "Date", "Arrived", "Departed", "Total Time", "Cost"]
    gap = 6
    label_w_total = sum(stringWidth(lbl, FONT, 9) for lbl in row_labels)
    blank_w = max(20, (usable_w - label_w_total - gap * 2 * len(row_labels)) / len(row_labels))
    parts = []
    for lbl in row_labels:
        parts.append(("text", lbl))
        parts.append(("blank", blank_w))
    _row(c, MARGIN_X, y, parts, gap=gap)
    y -= 16

    _row(c, MARGIN_X, y, [("text", "Work Completed:"), ("blank_to", PAGE_W - MARGIN_X)])
    y -= 16

    _row(
        c,
        MARGIN_X,
        y,
        [
            ("text", "Additional Work Needed:"),
            ("checkbox_label", "No"),
            ("checkbox_label", "Yes"),
            ("blank_to", PAGE_W - MARGIN_X),
        ],
    )
    y -= 16

    _row(c, MARGIN_X, y, [("text", "Drafting Time"), ("blank", 100)])
    y -= 14

    checklist_top = y - 4

    # Footer height is known ahead of time (fixed content), so we can size
    # the checklist area to fill exactly the space above it.
    footer_rows_h = (
        14  # results row 1
        + 14  # results row 2
        + 14  # materials row
        + 10  # gap
        + 11 * 2  # FOR ALL JOBS (2 lines)
        + 4
        + 11 * 2  # FOR SURVEYS (2 lines)
        + 8
        + 11  # "Notes" label
        + 14 * 3  # 3 note lines
    )
    footer_top = BOTTOM_Y + footer_rows_h

    checklist_h = checklist_top - footer_top
    overflow = _draw_checklist_area(c, checklists, MARGIN_X, checklist_top, PAGE_W - 2 * MARGIN_X, checklist_h)

    # ---- Draw fixed footer ----
    fy = footer_top
    _row(
        c,
        MARGIN_X,
        fy,
        [
            ("text", "All Property Corners Found"),
            ("checkbox_label", "Yes"),
            ("checkbox_label", "No"),
        ],
    )
    _row(
        c,
        PAGE_W / 2 + 10,
        fy,
        [
            ("text", "Missing Property Corners Set in Field"),
            ("checkbox_label", "Yes"),
            ("checkbox_label", "No"),
        ],
    )
    fy -= 14

    _row(
        c,
        MARGIN_X,
        fy,
        [
            ("text", "Need to Return to Set Missing Property Corners"),
            ("checkbox_label", "Yes"),
            ("checkbox_label", "No"),
        ],
    )
    fy -= 14

    _row(
        c,
        MARGIN_X,
        fy,
        [
            ("text", "Materials Used:"),
            ("checkbox_label", "Rebar: Quantity"),
            ("blank", 70),
            ("checkbox_label", "Wooden Stakes: Quantity"),
            ("blank", 70),
        ],
    )
    fy -= 20

    c.setFont(FONT, 7.5)
    for line in (
        "FOR ALL JOBS: take pictures including property, all 4 sides of all structures, fences, property corners, flagging, etc.",
        "FOR SURVEYS: sign & date sketch, building description & dimensions, all paved surfaces, fences, property corners, label",
        "streets, adjacent property corners, benchmark information, utilities, etc.",
    ):
        c.drawString(MARGIN_X, fy, line)
        fy -= 11
    fy -= 6

    c.setFont(FONT, 9)
    c.drawString(MARGIN_X, fy, "Notes")
    fy -= 14
    for _ in range(3):
        blank_line(c, MARGIN_X, PAGE_W - MARGIN_X, fy)
        fy -= 14

    c.showPage()
    c.save()
    return overflow
