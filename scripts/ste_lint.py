"""The lint loop and the report."""
import json
import re

from ste_lists import LIST_ITEM_INDENT, _dangling_conjunction_findings
from ste_markdown import (
    ANY_LIST_ITEM, BLOCKQUOTE_PREFIX, GITHUB_ALERT, HTML_BLOCK_TAG, NO_PARAGRAPH,
    SETEXT_UNDERLINE, STANDALONE_LINE, _blank_front_matter, _fence_ends_with_quote,
    _fence_step, _html_block_step, _indent_width, _strip_quotes,
)
from ste_rules import MODAL_PERFECT_PREFIX, RULES, SYNONYM_GROUPS
from ste_tables import _markdown_table_cells
from ste_text import (
    _long_sentence_findings, _mask_code_spans, _mask_inline_code, _mask_non_prose,
)


def _word_re(base):
    return re.compile(r"\b" + base + r"(?:s|es|ed|d|ing)?\b", re.I)


def lint(text, filename="<stdin>"):
    text = _blank_front_matter(text)
    findings = []
    words_total = 0
    fence = None
    html_block = None
    in_paragraph = False
    # content indent of the open list item, so its indented lines are not code
    list_indent = 0
    # backtick run length of a code span that is open across lines, or 0
    open_span = 0
    paragraph_depth = 0
    html_containers = []
    lines = text.splitlines()
    table_cells = _markdown_table_cells(lines)
    # first occurrence of each synonym-group member: (group_idx, base) -> (line, col, match)
    seen_synonyms = {}
    # consecutive prose lines form one block, so wrapped sentences count once
    block = []
    in_quote = False
    after_boundary = True

    def flush():
        findings.extend(_long_sentence_findings(block, filename))
        block.clear()

    for lineno, raw_line in enumerate(lines, 1):
        was_paragraph = in_paragraph
        if not raw_line.strip():
            open_span = 0
        if _fence_ends_with_quote(fence, raw_line):
            # The quote that holds the fence ended: judge this line as any other line.
            fence = None
        in_html = False
        if fence is None:
            in_html, html_block = _html_block_step(html_block, raw_line, in_paragraph)
        if in_html:
            # An HTML block holds literal text until it ends, so no fence opens in it.
            is_fence = False
        else:
            is_fence, fence = _fence_step(fence, raw_line)
        # A paragraph is open after a line of text that no other block takes.
        # The paragraph state reads the line after its quote prefix, so a line with only
        # quote markers is blank inside its quote.
        depth, unquoted = _strip_quotes(raw_line.expandtabs(4))
        underline = (in_paragraph and depth == paragraph_depth
                     and SETEXT_UNDERLINE.match(unquoted))
        in_paragraph = bool(unquoted.strip() and not in_html and not is_fence and not fence
                            and not NO_PARAGRAPH.match(unquoted) and not underline)
        if not in_paragraph:
            paragraph_depth = 0
        elif not was_paragraph or depth > paragraph_depth:
            paragraph_depth = depth
        # A lazy line with fewer ">" keeps the depth of the paragraph.
        if is_fence:
            flush()
            # A fence inside a quote does not start the quote: an alert marker after it is text.
            after_boundary = _strip_quotes(raw_line)[0] == 0
            continue
        if fence:
            continue
        # CommonMark 4.4: an indented code block. It cannot interrupt a paragraph.
        rest = _strip_quotes(raw_line.expandtabs(4))[1]
        indent = _indent_width(rest)
        if rest.strip() and not in_html and not was_paragraph:
            if indent >= list_indent + 4:
                in_paragraph = False
                continue
            item = LIST_ITEM_INDENT.match(rest)
            if item:
                list_indent = len(item.group(0)) if item.group(3) else len(item.group(0)) + 1
            elif indent < list_indent:
                list_indent = 0
        if HTML_BLOCK_TAG.match(raw_line.lstrip()):
            for tag in HTML_BLOCK_TAG.finditer(_mask_inline_code(raw_line)):
                name = tag.group(2).lower()
                if tag.group(1):
                    if name in html_containers:
                        while html_containers:
                            if html_containers.pop() == name:
                                break
                elif not tag.group().endswith("/>"):
                    html_containers.append(name)
        segments = table_cells.get(lineno - 1, [(raw_line, 0)])
        is_table = (lineno - 1) in table_cells
        quote = BLOCKQUOTE_PREFIX.match(raw_line)
        is_quote = bool(quote)
        # judge block boundaries on the text inside any blockquote prefix
        content = raw_line[quote.end():] if quote else raw_line
        # a GitHub alert marker is a label that stands alone, as a heading does.
        # Accept it only in an unindented quote of one level after a blank line,
        # a fence, or at the start of the text. Elsewhere a list item or a lazy
        # continuation line can hold the quote, and GitHub shows the marker as
        # text. Markers inside HTML containers are also plain text.
        alert = (not html_containers and raw_line.startswith(">") and after_boundary
                 and quote.group().count(">") == 1
                 and GITHUB_ALERT.fullmatch(content.strip()))
        standalone = STANDALONE_LINE.match(content) or alert
        if (is_table or not content.strip() or standalone
                or ANY_LIST_ITEM.match(content) or is_quote != in_quote):
            flush()
        in_quote = is_quote
        after_boundary = not raw_line.strip()
        for segment, source_column in segments:
            if is_table or in_html:
                # a table cell holds its own spans, and an HTML block has none
                line = _mask_non_prose(segment)
            else:
                masked, open_span = _mask_code_spans(segment, open_span, lines[lineno:])
                line = _mask_non_prose(masked)
            words_total += len(line.split())
            for rule_id, level, pattern, msg in RULES:
                for m in pattern.finditer(line):
                    # the modal may end the line before: "may" / "have failed"
                    before = (block[-1][2] + " " if block else "") + line[:m.start()]
                    if rule_id == "present-perfect" and MODAL_PERFECT_PREFIX.search(before):
                        continue
                    findings.append({"file": filename, "line": lineno,
                                     "col": source_column + m.start() + 1,
                                     "rule": rule_id, "level": level,
                                     "match": m.group(0), "message": msg})
            for gi, group in enumerate(SYNONYM_GROUPS):
                for base in group:
                    if (gi, base) in seen_synonyms:
                        continue
                    m = _word_re(base).search(line)
                    if m:
                        seen_synonyms[(gi, base)] = (
                            lineno, source_column + m.start() + 1, m.group(0)
                        )
            # the blockquote prefix and the list marker are markup, not words in the sentence
            skip = quote.end() if quote and not is_table else 0
            marker = None if is_table else ANY_LIST_ITEM.match(segment[skip:])
            if marker:
                skip += marker.end()
            if line[skip:].strip():
                block.append((lineno, source_column + skip, line[skip:]))
            if is_table:
                flush()  # each table cell is its own block
        if standalone:
            flush()
    flush()
    # synonym rotation: flag each member after the first, at its first occurrence
    for gi, group in enumerate(SYNONYM_GROUPS):
        present = [(seen_synonyms[(gi, b)], b) for b in group if (gi, b) in seen_synonyms]
        if len(present) > 1:
            present.sort()  # document order
            first_base = present[0][1]
            for (lineno, col, match), base in present[1:]:
                findings.append({"file": filename, "line": lineno, "col": col,
                                 "rule": "synonym-rotation", "level": "advisory-free",
                                 "match": match,
                                 "message": f"'{base}' and '{first_base}' name the same action. Pick one and use it every time."})
    findings.extend(_dangling_conjunction_findings(text, filename))
    findings.sort(key=lambda f: (f["line"], f["col"]))
    return findings, words_total


def report(findings, words_total, as_json, hard_count, baseline):
    rate = round(len(findings) * 100 / words_total, 1) if words_total else 0.0
    if as_json:
        print(json.dumps({"violations": findings, "count": len(findings),
                          "hard_count": hard_count, "baseline": baseline,
                          "words": words_total, "per_100_words": rate}, indent=2))
        return
    for f in findings:
        print(f"{f['file']}:{f['line']}:{f['col']} {f['rule']}: {f['message']} [{f['match']}]")
    print(f"\n{len(findings)} violations ({hard_count} hard, baseline {baseline}), "
          f"{words_total} words, {rate} per 100 words")
    print("Hedges/modality (may, might, could) are never flagged: confidence is content.")
