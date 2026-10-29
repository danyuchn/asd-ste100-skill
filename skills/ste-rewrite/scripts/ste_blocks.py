"""Document structure for ste-lint.

The scanner turns Markdown into prose blocks with true line and column
positions. It blanks markup and never removes it, so each column stays true.
A block is a list of (line, column, text) pieces that belong to one paragraph,
one heading, one list item, or one table cell. The scanner also records each
list item that ends with "and" or "or".
"""
import re

from ste_tables import is_separator, read_table, split_row
from ste_text import KEEP, LINE_BREAK, indent_of, mask, prefix_length, view
from ste_words import ALERT_WORDS, LIST_CONJUNCTIONS

FRONT_MATTER = "---"
COMMENT_OPEN = "<!--"
COMMENT_CLOSE = "-->"
HTML_OPEN = "<"
QUOTE_MARK = ">"
BACKTICK = "`"
FENCE_ROOM = 3      # a fence may start up to 3 spaces inside its own block
CODE_INDENT = 4     # 4 spaces of indentation make a code block
TOP_QUOTE = 1       # a GitHub alert marker works in a quote of depth 1 only
BLANK = " "
MIN_THEMATIC_MARKS = 3   # CommonMark: a thematic break needs 3 marks
MAX_LIST_DIGITS = 9      # CommonMark: an ordered list number has 1 to 9 digits
MAX_MARKER_INDENT = 3    # CommonMark: a marker may sit up to 3 spaces in
HEADING_LEVELS = 6       # CommonMark: ATX headings run from # to ######

FENCE = re.compile(r"(?P<indent> *)(?P<chars>`{3,}|~{3,})(?P<info>.*)")
REFDEF = re.compile(r"^ {0,%d}\[" % MAX_MARKER_INDENT + r"(?!\^)[^\]]+\]:\s")
COMMENT = re.compile(COMMENT_OPEN + r".*?" + COMMENT_CLOSE)
LIST_ITEM = re.compile(r"^( *)([-*+]|[0-9]{1,%d}[.)])(?:[ \t]+|$)" % MAX_LIST_DIGITS)
THEMATIC = re.compile(r"^ {0,%d}(?:[-*_=] *){%d,}$" % (MAX_MARKER_INDENT, MIN_THEMATIC_MARKS))
HEADING = re.compile(r"^ {0,%d}#{1,%d}(?: |$)" % (MAX_MARKER_INDENT, HEADING_LEVELS))
ALERT = re.compile(r"\[!(?:" + "|".join(ALERT_WORDS) + r")\]", re.I)
CONJUNCTION = re.compile(r"\b(" + "|".join(LIST_CONJUNCTIONS) + r")\s*$", re.I)


class Scanner:
    """One pass over the lines of a document."""

    def __init__(self, text):
        self.lines = LINE_BREAK.split(text)
        self.blocks = []
        self.current = []
        self.dangling = []
        self.fence = None
        self.comment = False
        self.list_open = False
        self.prev_text = False
        self.prev_quote = False
        self.item = None
        self.index = 0

    def _cut(self):
        if self.current:
            self.blocks.append(self.current)
            self.current = []

    def _close_item(self):
        """End the open list item and record a conjunction at its end."""
        if self.item and self.item["last"]:
            lineno, tail = self.item["last"]
            found = CONJUNCTION.search(tail)
            if found:
                col = (self.item["col"] if lineno == self.item["line"]
                       else found.start(1) + 1)
                self.dangling.append((lineno, col, found.group(1)))
        self.item = None

    def _open_item(self, lineno, marker):
        self._cut()
        self.list_open = True
        self.item = {"line": lineno, "col": marker.start(2) + 1, "last": None,
                     "indent": max(marker.end(), marker.end(2) + 1)}

    def _fence_match(self, raw):
        pre = prefix_length(raw)
        found = FENCE.fullmatch(raw[pre:].rstrip())
        # Inside a list item a fence sits at the content column of the item.
        room = FENCE_ROOM + (self.item["indent"] if self.item else 0)
        if found and len(found.group("indent")) > room:
            return None
        return found

    def _closes_fence(self, found):
        chars = found.group("chars")
        return (chars[0] == self.fence[0] and len(chars) >= len(self.fence)
                and not found.group("info").strip())

    def _fence_step(self, raw):
        """Handle a fence line or a line inside a fence. True when consumed."""
        if self.comment:
            return False
        found = self._fence_match(raw)
        if self.fence:
            if found and self._closes_fence(found):
                self.fence = None
                self._cut()
            return True
        if found and not (found.group("chars")[0] == BACKTICK
                          and BACKTICK in found.group("info")):
            self.fence = found.group("chars")
            self._cut()
            return True
        return False

    def _comment_step(self, raw):
        """Handle a line inside an HTML comment. True when consumed."""
        if not self.comment:
            return False
        self._cut()
        self.comment = COMMENT_CLOSE not in raw
        return True

    def _blank_comment(self, raw):
        """Blank each closed comment, and the tail of a comment that stays open."""
        line = COMMENT.sub(lambda m: BLANK * len(m.group()), raw)
        start = line.find(COMMENT_OPEN)
        if start >= 0:
            self.comment = True
            line = line[:start] + BLANK * (len(line) - start)
        return line

    def _skip_front_matter(self):
        if self.lines and self.lines[0].strip() == FRONT_MATTER:
            for number, line in enumerate(self.lines[1:], start=1):
                if line.strip() == FRONT_MATTER:
                    self.index = number + 1
                    return

    def _table_step(self, text_line, pre):
        """Read a whole table and give each cell its own block. True when read."""
        if self.index >= len(self.lines):
            return False
        header = split_row(text_line, pre)
        if not header:
            return False
        separator = split_row(self.lines[self.index], prefix_length(self.lines[self.index]))
        if not is_separator(separator, len(header)):
            return False
        self._cut()
        rows, self.index = read_table(self.lines, self.index, header)
        for lineno, row in rows:
            for cell, col in row:
                if cell:
                    self.blocks.append([(lineno, col, cell)])
        self.prev_text = False
        return True

    def run(self):
        self._skip_front_matter()
        while self.index < len(self.lines):
            raw = self.lines[self.index]
            lineno = self.index + 1
            self.index += 1
            self._line(raw, lineno)
        self._cut()
        self._close_item()
        return self.blocks, self.dangling

    def _line(self, raw, lineno):
        if self._fence_step(raw) or self._comment_step(raw):
            return
        if not raw.strip():
            self._cut()
            self.prev_text = self.prev_quote = False
            return
        if REFDEF.match(raw):
            self._cut()
            self.prev_text = False
            return
        line = self._blank_comment(raw)
        text_line, pre = view(line)
        quoted = pre > 0
        body = line[pre:]
        indent = indent_of(body)
        marker = LIST_ITEM.match(body)
        starts_item = bool(marker) and not THEMATIC.match(body)
        if self.item and (starts_item or quoted or indent < self.item["indent"]):
            self._close_item()
        if not starts_item and not quoted and indent == 0:
            self.list_open = False
        was_quote, self.prev_quote = self.prev_quote, quoted
        if quoted != was_quote:
            self._cut()
        if raw[pre:].lstrip().startswith(HTML_OPEN) or (
                indent >= CODE_INDENT and not self.list_open
                and not self.prev_text and not quoted):
            self._cut()
            self.prev_text = False
            return
        # A GitHub alert marker is markup only on the first line of a top quote.
        if (quoted and not was_quote and line[:pre].count(QUOTE_MARK) == TOP_QUOTE
                and ALERT.fullmatch(body.strip())):
            return
        heading = HEADING.match(body)
        if THEMATIC.match(body) or heading:
            self._cut()
            self.prev_text = False
            if heading:
                end = pre + heading.end()
                self.current.append((lineno, 0, BLANK * end + text_line[end:]))
                self._cut()
            return
        if not starts_item and self._table_step(text_line, pre):
            return
        item_text = mask(line, KEEP)
        if starts_item:
            end = pre + marker.end()
            text_line = BLANK * end + text_line[end:]
            item_text = BLANK * end + item_text[end:]
            self._cut()
            self.list_open = True
            if quoted:
                self.item = None
            else:
                self._open_item(lineno, marker)
        if self.item and item_text.strip():
            self.item["last"] = (lineno, item_text)
        if text_line.strip():
            self.current.append((lineno, 0, text_line))
        self.prev_text = True


def scan(text):
    """Return (blocks, dangling) for one document."""
    return Scanner(text).run()
