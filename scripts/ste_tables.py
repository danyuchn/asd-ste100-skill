"""Markdown table detection: split rows and map table cells."""
import re


TABLE_SEPARATOR_CELL = re.compile(r"^:?-+:?$")


def _split_table_row(line):
    """Return trimmed table cells and their zero-based source columns.

    A row needs a leading or trailing pipe, or a pipe between two cells.
    Escaped pipes stay in their cell. This deliberately implements only the
    ordinary Markdown table shape; it is enough to distinguish a table from
    prose that happens to contain a pipe.
    """
    left = len(line) - len(line.lstrip())
    right = len(line.rstrip())
    content = line[left:right]
    if "|" not in content:
        return None
    edge_pipe = False
    if content.startswith("|"):
        content = content[1:]
        left += 1
        edge_pipe = True
    if content.endswith("|"):
        content = content[:-1]
        edge_pipe = True
    raw_cells = re.split(r"(?<!\\)\|", content)
    if len(raw_cells) < 2 and not edge_pipe:
        return None

    cells = []
    column = left
    for raw_cell in raw_cells:
        leading = len(raw_cell) - len(raw_cell.lstrip())
        cells.append((raw_cell.strip(), column + leading))
        column += len(raw_cell) + 1
    return cells


def _markdown_table_cells(lines):
    """Map ordinary Markdown table rows to their prose cells.

    The separator row anchors detection, so pipe-containing prose is not
    treated as a table. Both leading-pipe and no-leading-pipe table styles are
    accepted. As in GFM, the header and separator must have the same number of
    cells, but a body row may have fewer or more. A line without a pipe ends
    the table.
    """
    table_cells = {}
    index = 1
    while index < len(lines):
        separator = _split_table_row(lines[index])
        header = _split_table_row(lines[index - 1])
        if (not separator or not header or len(separator) != len(header)
                or not all(TABLE_SEPARATOR_CELL.fullmatch(cell)
                           for cell, _ in separator)):
            index += 1
            continue

        table_cells[index - 1] = header
        table_cells[index] = []
        index += 1
        while index < len(lines):
            row = _split_table_row(lines[index])
            if not row:
                break
            table_cells[index] = row
            index += 1
    return table_cells
