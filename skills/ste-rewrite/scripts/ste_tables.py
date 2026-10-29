"""Markdown tables for ste-lint.

Each cell is its own text, because a cell is not a sentence of its neighbor.
"""
import re

from ste_text import view

CELL_BORDER = "|"
ESCAPED_BORDER = "\\|"
UNESCAPED_BORDER = re.compile(r"(?<!\\)\|")
MIN_SEPARATOR_DASHES = 3  # CommonMark: a delimiter cell holds at least 3 dashes
SEPARATOR_CELL = re.compile(r":?-{%d,}:?" % MIN_SEPARATOR_DASHES)
MIN_CELLS = 2  # one border makes two cells; fewer means the line is plain prose


def split_row(text, start=0):
    """Return [(cell, column)] for a table row, or None when it is not one."""
    row = text[start:]
    if CELL_BORDER not in row:
        return None
    col = start + len(row) - len(row.lstrip())
    row = row.strip()
    if row.startswith(CELL_BORDER):
        row, col = row[len(CELL_BORDER):], col + len(CELL_BORDER)
    if row.endswith(CELL_BORDER) and not row.endswith(ESCAPED_BORDER):
        row = row[:-len(CELL_BORDER)]
    parts = UNESCAPED_BORDER.split(row)
    if len(parts) < MIN_CELLS:
        return None
    cells = []
    for part in parts:
        cells.append((part.strip(), col + len(part) - len(part.lstrip())))
        col += len(part) + len(CELL_BORDER)
    return cells


def is_separator(cells, width):
    return (cells is not None and len(cells) == width
            and all(SEPARATOR_CELL.fullmatch(cell) for cell, _ in cells))


def read_table(lines, index, header):
    """Read the body rows of a table. Return (rows, next index).

    `index` points at the separator line. `header` is the split header row.
    """
    rows = [(index, header)]  # the header sits one line above the separator
    index += 1
    while index < len(lines):
        row_text, row_pre = view(lines[index])
        row = split_row(row_text, row_pre)
        if not row or len(row) != len(header):
            break
        index += 1
        rows.append((index, row))
    return rows, index
