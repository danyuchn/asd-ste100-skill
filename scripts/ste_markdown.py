"""Markdown block state: fences, quotes, HTML blocks, and front matter."""
import re


CODE_FENCE = re.compile(r"^(`{3,}|~{3,})")
# Headings, thematic breaks, front-matter delimiters, and HTML lines stand alone.
STANDALONE_LINE = re.compile(r"^ {0,3}(?:#|<|(?:[-*_=] *){3,}$)")
BLOCKQUOTE_PREFIX = re.compile(r"^ {0,3}(?:> ?)+")
# A GitHub alert marker, alone on the first line of a quote: "> [!NOTE]".
GITHUB_ALERT = re.compile(r"\[!(?:note|tip|important|warning|caution)\]", re.I)
# Track ordinary block containers, not inline or void tags such as span or hr.
HTML_BLOCK_TAG = re.compile(
    r"<(/?)(address|article|aside|blockquote|body|caption|center|dd|details|"
    r"dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|h[1-6]|"
    r"header|hgroup|html|iframe|legend|li|main|menu|nav|noframes|ol|"
    r"optgroup|option|p|pre|script|search|section|style|summary|table|"
    r"tbody|td|textarea|tfoot|th|thead|title|tr|ul)(?=[\s/>])[^>]*>", re.I,
)
# Any list marker at any depth starts a new prose block.
ANY_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])(?:\s|$)")


# One blockquote level: up to three spaces, ">", and one optional space.
QUOTE_LEVEL = re.compile(r" {0,3}> ?")


def _strip_quotes(line, depth=None):
    """Return (levels, rest): the blockquote levels that start LINE and the text after them.

    With DEPTH, remove at most DEPTH levels: a deeper ">" is content.
    """
    levels, pos = 0, 0
    while depth is None or levels < depth:
        level = QUOTE_LEVEL.match(line, pos)
        if not level:
            break
        levels, pos = levels + 1, level.end()
    return levels, line[pos:]


def _indent_width(text):
    """Columns of the spaces and tabs that start TEXT, with a tab stop of 4."""
    return len(text[:len(text) - len(text.lstrip(" \t"))].expandtabs(4))


def _fence_ends_with_quote(fence, line):
    """True when LINE has fewer blockquote levels than the open FENCE."""
    return fence is not None and _strip_quotes(line.expandtabs(4), fence[1])[0] < fence[1]


def _fence_step(fence, line):
    """Return (is_fence_line, open_fence) after LINE.

    FENCE is None, or the open fence as (run, quote depth, indent). This follows
    CommonMark 4.5 for blockquotes and for the fence itself: a fence in a blockquote
    ends when its quote ends. Only a run of the same character, at least as long,
    with only spaces or tabs after it, closes the block. A backtick fence has no
    backtick in its info string. List items are not tracked, so the indent of a
    fence is not limited to three columns. A closing fence may have at most three
    columns more indent than the opening fence, also at the top level.
    """
    # Tabs become spaces from the real column, so a tab after ">" counts correctly.
    line = line.expandtabs(4)
    if fence is None:
        depth, rest = _strip_quotes(line)
        content = rest.lstrip(" \t")
        marker = CODE_FENCE.match(content)
        if not marker:
            return False, None
        run = marker.group(1)
        if run[0] == "`" and "`" in content[marker.end():]:
            return False, None
        return True, (run, depth, _indent_width(rest))
    if _fence_ends_with_quote(fence, line):
        # The quote that holds the fence ended, so the fence ended too.
        return _fence_step(None, line)
    run, depth, indent = fence
    rest = _strip_quotes(line, depth)[1]
    content = rest.lstrip(" \t")
    marker = CODE_FENCE.match(content)
    if (marker and marker.group(1)[0] == run[0] and len(marker.group(1)) >= len(run)
            and _indent_width(rest) <= indent + 3
            and not content[marker.end():].strip(" \t")):
        return True, None
    return False, fence


# CommonMark 4.6: how each kind of HTML block starts, and the text that ends it.
# None: the block ends at a blank line (types 6 and 7).
_BLOCK_TAGS = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|"
    "details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|"
    "h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|"
    "optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|"
    "tr|track|ul"
)
HTML_BLOCK_KINDS = [
    (re.compile(r"^ {0,3}<(?:script|pre|style|textarea)(?:\s|>|$)", re.I),
     re.compile(r"</(?:script|pre|style|textarea)>", re.I)),
    (re.compile(r"^ {0,3}<!--"), re.compile(r"-->")),
    (re.compile(r"^ {0,3}<\?"), re.compile(r"\?>")),
    (re.compile(r"^ {0,3}<!\[CDATA\["), re.compile(r"\]\]>")),
    (re.compile(r"^ {0,3}<![A-Za-z]"), re.compile(r">")),
    (re.compile(rf"^ {{0,3}}</?(?:{_BLOCK_TAGS})(?:\s|/?>|$)", re.I), None),
]
# Type 7: one complete open or closing tag alone on its line (CommonMark 6.6 grammar).
# It cannot interrupt a paragraph.
_ATTRIBUTE = (r"\s+[A-Za-z_:][A-Za-z0-9_.:-]*"
              r"(?:\s*=\s*(?:[^\s\"'=<>`]+|'[^']*'|\"[^\"]*\"))?")
HTML_TYPE7 = re.compile(
    rf"^ {{0,3}}(?:<[A-Za-z][A-Za-z0-9-]*(?:{_ATTRIBUTE})*\s*/?>|</[A-Za-z][A-Za-z0-9-]*\s*>)\s*$")
# A heading or a thematic break ends a paragraph and is no paragraph line.
NO_PARAGRAPH = re.compile(r"^ {0,3}(?:#{1,6}(?:\s|$)|(?:[-*_][ \t]*){3,}$)")


def _html_block_step(block, line, in_paragraph):
    """Return (in_html_block, open_block) for LINE.

    BLOCK is None, False (an HTML block that ends at a blank line), or the pattern
    that ends the open block. IN_PARAGRAPH: a paragraph is open before LINE. A ">"
    in an HTML block is text, so it opens no fence.
    """
    if block is None:
        for start, end in HTML_BLOCK_KINDS:
            if start.match(line):
                block = False if end is None else end
                break
        else:
            if in_paragraph or not HTML_TYPE7.match(line):
                return False, None
            block = False
    if block is False:
        return bool(line.strip()), (block if line.strip() else None)
    return True, (None if block.search(line) else block)


def _blank_front_matter(text):
    """Blank a leading YAML front-matter block, keeping line numbers.

    Front matter is metadata, not prose: without this, its keys and values
    join into one sentence.
    """
    lines = text.splitlines()
    if lines and lines[0].rstrip() == "---":
        for end in range(1, len(lines)):
            if lines[end].rstrip() == "---":
                return "\n" * (end + 1) + "\n".join(lines[end + 1:])
    return text
