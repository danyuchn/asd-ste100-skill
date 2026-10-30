#!/usr/bin/env python3
"""Deterministic linter for the structural STE rules in SKILL.md.

Checks only rules verifiable without ASD's dictionary. Deliberately never
flags hedges or modality (may/might/could): the skill treats confidence as
content, and a linter that pressures hedges out would rewrite claims.

Usage:
    ste-lint.py FILE [FILE ...]
    echo "text" | ste-lint.py [--json]
    ste-lint.py --baseline 5 FILE      # pass unless hard violations exceed 5
    ste-lint.py --disable passive-voice,present-perfect FILE
    ste-lint.py --selftest

Exit 1 when hard ("advisory-free") violations exceed the baseline (default 0).
Advisory findings (passive voice, compound tenses) never fail the run.
Exit 2 on a usage error (unknown flag, bad value, unknown rule, unreadable file).
"""
import argparse
import bisect
import contextlib
import io
import json
import os
import re
import sys
import tempfile

# ponytail: regex heuristics, not a parser. No noun-cluster rule — needs POS
# tagging to avoid constant false positives; add spaCy-backed rule if ever needed.
# No ellipsis rule by owner's choice: technical writing sometimes earns one.
# Irregular past participles used by the present-perfect heuristic.
IRREGULAR_PARTICIPLES = "given|taken|made|done|found|seen|known|shown|written|built|sent|set|run|read|kept|held|left|put|cut|hit|let|shut|split|spread|begun|become|come|gone|got|gotten|lost|met|paid|said|sold|told|thought|brought|bought|caught|taught|won|worn|torn|born|drawn|grown|thrown|flown|driven|risen|chosen|broken|spoken|frozen|hidden|ridden|forgotten|fallen|eaten|beaten|understood|stood|struck|stuck|swung|hung|led|fed|bled|fled|sped|bound|wound|dug|spun|slid|bit|lit|quit"

# Preserve the original passive heuristic; perfects also include intransitive verbs.
PASSIVE_PARTICIPLES = "given|taken|made|done|found|seen|known|shown|written|built|sent|set|run|read|kept|held|left|put"
MODAL_PERFECT_PREFIX = re.compile(
    r"\b(?:may|might|could|should|would|must|can|will|shall)"
    r"(?:\s+not|n['’]t)?\s+$", re.I,
)

RULES = [
    ("semicolon", "advisory-free",
     re.compile(r";"),
     "STE bans the semicolon (Rule 8.1). Split into separate sentences."),
    ("phrasal-verb", "advisory-free",
     re.compile(r"\b(spin(?:ning|s)? up|spun up|reach(?:ing|es|ed)? out|div(?:e|es|ing|ed) into|dove into|kick(?:ing|s|ed)? off|circl(?:e|es|ing|ed) back|touch(?:ing|es|ed)? base)\b", re.I),
     "Soft phrasal verb. Use the single plain verb (start, contact, read, begin)."),
    ("marketing-adjective", "advisory-free",
     re.compile(r"\b(seamless(?:ly)?|robust(?:ly)?|cutting-edge|effortless(?:ly)?|blazing[- ]fast|world-class|state-of-the-art|game-chang(?:ing|er))\b", re.I),
     "Marketing adjective. Delete, or replace with the measurement that earns the claim."),
    ("nominalization", "advisory-free",
     re.compile(r"\b(perform|performs|performed|conduct|conducts|conducted|carry out|carries out|carried out)\s+(?:a|an|the)\s+\w+(?:tion|sion|ment|ance|ence|ysis)\b", re.I),
     "Action frozen into a noun. Use the verb (analyze, not perform an analysis of)."),
    ("passive-voice", "advisory",
     re.compile(r"\b(is|are|was|were|been|being)\s+(\w+ed|" + PASSIVE_PARTICIPLES + r")\b(?!\s+(?:to|for|by)\s+\w+ing)", re.I),
     "Possible passive voice. Name the actor and use an active verb, unless the actor is unknown or irrelevant."),
    ("present-perfect", "advisory",
     # modal + perfect infinitive ("may have failed") is a protected hedge, not present perfect
     re.compile(r"(?<!\bmay )(?<!\bmight )(?<!\bcould )(?<!\bshould )(?<!\bwould )(?<!\bmust )\b(has|have|had)\s+(?:been\s+)?(?:\w+(?:ed|en)|" + IRREGULAR_PARTICIPLES + r")\b", re.I),
     "Compound tense. Use simple past/present unless current relevance is the point (then keep and flag)."),
]

# One word, one meaning: groups of verbs commonly rotated for the same action.
# Only pairs where the members are genuinely interchangeable — error/fault/failure
# are distinct concepts and stay out.
SYNONYM_GROUPS = [
    ("check", "verify", "confirm", "validate"),
    ("delete", "remove", "erase"),
    ("start", "launch", "begin", "initiate"),
    ("stop", "halt", "terminate"),
    ("show", "display"),
    ("use", "utilize", "employ"),
    ("fix", "repair", "correct"),
    ("send", "transmit"),
    ("get", "retrieve", "fetch", "obtain"),
    ("change", "modify", "alter"),
]

MAX_WORDS = 25  # descriptions cap; instructions cap is 20 but undetectable without context

CODE_FENCE = re.compile(r"^(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`[^`]*`")
LIST_ITEM_START = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>[-*+]|[0-9]+[.)])(?P<gap> +)(?P<body>.*)$"
)
CONJUNCTION_END = re.compile(r"\b(?:and|or)\s*$", re.I)
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
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
# A letter or a digit: a token without one is punctuation, not a word.
WORD_CHAR = re.compile(r"[^\W_]")
# A token that ends in terminal punctuation, optionally followed by closing
# quotes, brackets, or Markdown emphasis markers ("**Lead.**").
SENTENCE_END = re.compile(r"[.!?][\"'”’)\]*_]*$")
OPENERS = "\"'“‘([*_"
# Abbreviations whose period never ends a sentence.
ABBREVIATIONS = {"vs.", "cf.", "approx.", "mr.", "mrs.", "ms.", "dr.", "fig.", "no."}
# Dotted initialisms such as "e.g." and "U.S." end a sentence only when the
# next word starts with a capital letter.
DOTTED_ABBREVIATION = re.compile(r"(?:[a-z]\.){2,}", re.I)


def _word_re(base):
    return re.compile(r"\b" + base + r"(?:s|es|ed|d|ing)?\b", re.I)


def _count_words(text):
    """Count whitespace-separated tokens that contain a letter or a digit.

    Bare punctuation is not a word: a comma left behind by a masked code
    span, or a spaced em dash, does not make a sentence longer.
    """
    return sum(1 for token in text.split() if WORD_CHAR.search(token))


def _mask_inline_code(text):
    """Blank code spans with equal-length spaces so columns stay true."""
    return INLINE_CODE.sub(lambda match: " " * len(match.group(0)), text)


def _sentence_starts(text):
    """Return the offset of each sentence start in text.

    A sentence ends at a word that ends in terminal punctuation, after any
    closing quotes or brackets. Known abbreviations do not end a sentence.
    One pass over the words keeps the cost linear in the text length.
    """
    words = list(re.finditer(r"\S+", text))
    if not words:
        return [0]
    starts = [words[0].start()]
    for word, next_word in zip(words, words[1:]):
        end = SENTENCE_END.search(word.group())
        if not end:
            continue
        core = word.group()[:end.start() + 1].lstrip(OPENERS)
        if core.lower() in ABBREVIATIONS:
            continue
        if (DOTTED_ABBREVIATION.fullmatch(core)
                and not next_word.group().lstrip(OPENERS)[:1].isupper()):
            continue
        starts.append(next_word.start())
    return starts


def _long_sentence_findings(pieces, filename):
    """Flag long sentences in one prose block.

    pieces is a list of (lineno, source_column, text) tuples. The texts are
    joined with spaces, so a sentence wrapped across source lines is counted
    once, and each finding points at the line and column where it starts.
    """
    offsets, position = [], 0
    for _, _, text in pieces:
        offsets.append(position)
        position += len(text) + 1
    joined = " ".join(text for _, _, text in pieces)
    findings = []
    starts = _sentence_starts(joined)
    for start, end in zip(starts, starts[1:] + [len(joined)]):
        n = _count_words(joined[start:end])
        if n <= MAX_WORDS:
            continue
        index = bisect.bisect_right(offsets, start) - 1
        offset = offsets[index]
        lineno, source_column, _ = pieces[index]
        findings.append({"file": filename, "line": lineno,
                         "col": source_column + start - offset + 1,
                         "rule": "long-sentence", "level": "advisory-free",
                         "match": f"{n} words",
                         "message": f"Sentence has {n} words (cap {MAX_WORDS}). Split it."})
    return findings


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
# Type 7: one complete open or closing tag alone on its line. It cannot interrupt a paragraph.
HTML_TYPE7 = re.compile(
    r"^ {0,3}(?:<[A-Za-z][A-Za-z0-9-]*(?:\s+[^<>]*?)?\s*/?>|</[A-Za-z][A-Za-z0-9-]*\s*>)\s*$")


def _html_block_step(block, line, after_blank):
    """Return (in_html_block, open_block) for LINE.

    BLOCK is None, False (an HTML block that ends at a blank line), or the pattern
    that ends the open block. AFTER_BLANK: the line before LINE is blank, or LINE is
    the first line. A ">" in an HTML block is text, so it opens no fence.
    """
    if block is None:
        for start, end in HTML_BLOCK_KINDS:
            if start.match(line):
                block = False if end is None else end
                break
        else:
            if not (after_blank and HTML_TYPE7.match(line)):
                return False, None
            block = False
    if block is False:
        return bool(line.strip()), (block if line.strip() else None)
    return True, (None if block.search(line) else block)


def _leading_spaces(line):
    return len(line) - len(line.lstrip(" "))


def _is_list_continuation(line, content_indent):
    if not line.strip():
        return True
    if LIST_ITEM_START.match(line):
        return False
    return len(line[:len(line) - len(line.lstrip(" \t"))].expandtabs(4)) >= content_indent


def _split_table_row(line):
    """Return trimmed table cells and their zero-based source columns.

    A pipe must separate at least two cells. Escaped pipes stay in their cell.
    This deliberately implements only the ordinary Markdown table shape; it is
    enough to distinguish a table from prose that happens to contain a pipe.
    """
    left = len(line) - len(line.lstrip())
    right = len(line.rstrip())
    content = line[left:right]
    if "|" not in content:
        return None
    if content.startswith("|"):
        content = content[1:]
        left += 1
    if content.endswith("|"):
        content = content[:-1]
    raw_cells = re.split(r"(?<!\\)\|", content)
    if len(raw_cells) < 2:
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
    accepted when their header and body use the same number of cells.
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
            if not row or len(row) != len(separator):
                break
            table_cells[index] = row
            index += 1
    return table_cells


def _dangling_conjunction_findings(text, filename):
    lines = text.splitlines()
    findings = []
    fence = None
    index = 0
    while index < len(lines):
        line = lines[index]
        is_fence, fence = _fence_step(fence, line)
        if is_fence or fence:
            index += 1
            continue
        start = LIST_ITEM_START.match(line)
        if not start:
            index += 1
            continue

        content_indent = (len(start.group("indent"))
                          + len(start.group("marker"))
                          + len(start.group("gap")))
        item_lines = [(index, start.group("body"))]
        next_index = index + 1
        item_fence = None
        while next_index < len(lines):
            candidate = lines[next_index]
            if _fence_ends_with_quote(item_fence, candidate):
                # The quote of the fence ended: judge this line as any other line.
                item_fence = None
            # A line outside the item ends it, also when it opens a fence.
            if item_fence is None and not _is_list_continuation(candidate, content_indent):
                break
            # Fence delimiters are state markers, not meaningful item lines.
            is_fence, item_fence = _fence_step(item_fence, candidate)
            if is_fence or item_fence:
                next_index += 1
                continue
            item_lines.append((next_index, candidate))
            next_index += 1

        meaningful = []
        for line_index, item_line in item_lines:
            # Preserve code spans as neutral operands while ignoring their contents.
            cleaned = INLINE_CODE.sub(" CODE ", item_line).strip()
            if cleaned:
                meaningful.append((line_index, cleaned))
        if meaningful:
            end_line_index, end_line = meaningful[-1]
            conjunction = CONJUNCTION_END.search(end_line)
        else:
            end_line_index, end_line, conjunction = None, None, None
        if conjunction:
            if end_line_index == index:
                finding_line = index + 1
                finding_col = start.start("marker") + 1
            else:
                raw_end_line = next(
                    raw for line_index, raw in item_lines
                    if line_index == end_line_index
                )
                masked_end_line = INLINE_CODE.sub(
                    lambda match: " " * len(match.group(0)), raw_end_line
                )
                raw_conjunction = CONJUNCTION_END.search(masked_end_line)
                finding_line = end_line_index + 1
                finding_col = raw_conjunction.start() + 1 if raw_conjunction else 1
            findings.append({
                "file": filename,
                "line": finding_line,
                "col": finding_col,
                "rule": "dangling-conjunction",
                "level": "advisory-free",
                "match": end_line,
                "message": "List item ends with a coordinating conjunction. Complete the item or join it with the next item.",
            })
        index = next_index
    return findings


def lint(text, filename="<stdin>"):
    findings = []
    words_total = 0
    fence = None
    html_block = None
    after_blank_line = True
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
        in_html = False
        if fence is None:
            in_html, html_block = _html_block_step(html_block, raw_line, after_blank_line)
        after_blank_line = not raw_line.strip()
        if in_html and _strip_quotes(raw_line.expandtabs(4))[0]:
            # In an HTML block, ">" is literal text, so it cannot open a quoted fence.
            is_fence = False
        else:
            is_fence, fence = _fence_step(fence, raw_line)
        if is_fence:
            flush()
            # A fence inside a quote does not start the quote: an alert marker after it is text.
            after_boundary = _strip_quotes(raw_line)[0] == 0
            continue
        if fence:
            continue
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
            line = _mask_inline_code(segment)
            words_total += len(line.split())
            for rule_id, level, pattern, msg in RULES:
                for m in pattern.finditer(line):
                    if rule_id == "present-perfect" and MODAL_PERFECT_PREFIX.search(
                        line[:m.start()]
                    ):
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


def selftest():
    bad = ("The panel is removed; spin up the job. "
           "Perform an analysis of the seamless log. "
           "We have received the report.")
    findings, _ = lint(bad)
    rules = {f["rule"] for f in findings}
    for expected in ("semicolon", "phrasal-verb", "nominalization",
                     "marketing-adjective", "passive-voice", "present-perfect"):
        assert expected in rules, expected
    # hedges must never be flagged, including modal + perfect infinitive
    findings, _ = lint("The request may have failed. It could be a timeout. "
                       "The disk might have filled.")
    assert findings == [], findings
    # irregular participles: "has run" is a compound tense as much as "has failed"
    findings, _ = lint("The task has run. The job has set the flag. We have begun.")
    assert sum(1 for f in findings if f["rule"] == "present-perfect") == 3, findings
    findings, _ = lint("The job may have run.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    # Modal perfects remain protected across negation and variable whitespace.
    for modal in ("may", "might", "could", "should", "would", "must"):
        for gap in (" ", "  ", "\t", " not "):
            findings, _ = lint(f"The task {modal}{gap}have run.")
            assert not any(f["rule"] == "present-perfect" for f in findings), findings
    findings, _ = lint("The task couldn't have run. The task MAY NOT HAVE RUN.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    findings, _ = lint("The task has run. We have begun. The flag is set.")
    assert sum(f["rule"] == "present-perfect" for f in findings) == 2, findings
    assert any(f["rule"] == "passive-voice" for f in findings), findings
    findings, _ = lint("The task is gone.")
    assert not any(f["rule"] == "passive-voice" for f in findings), findings
    # code blocks skipped
    findings, _ = lint("```\nx = a; y = b\n```")
    assert findings == []
    # a fence closes only on the same character, at least as long, with nothing after it
    for text in ("````md\n```\n````\n\nProse; here.",
                 "```\n~~~\n```\n\nProse; here.",
                 "~~~~\n~~~\n~~~~\n\nProse; here."):
        findings, _ = lint(text)
        assert [f["rule"] for f in findings] == ["semicolon"], (text, findings)
    findings, _ = lint("```\n```sh\nx = a; y = b\n```")
    assert findings == [], findings
    # a fence inside a blockquote is a fence
    findings, _ = lint("Text.\n\n> ```\n> x = a; y = b\n> ```\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 7)], findings
    # the dangling-conjunction rule uses the same fence state
    findings, _ = lint("````md\n```\n- Do this and\n````")
    assert findings == [], findings
    findings, _ = lint("- Do this\n  ````md\n  ```\n  code and\n  ````\n- Do that")
    assert findings == [], findings
    # a quoted fence ends with its quote, and a deeper ">" in a fence is code
    for text, lines in (("> ```\n> code\n\nProse; here.", [4]),
                        ("```\n> ```\nx; y\n```\n\nProse; here.", [6]),
                        (">  > ```\n>  > x; y\n>  > ```\n\nProse; here.", [5]),
                        ("> ```\n>     ```\n> x; y\n> ```\n\nProse; here.", [6]),
                        ("```foo`bar\nProse; here.", [2]),
                        ("```\nx; y\n```` \t\n\nProse; here.", [5])):
        findings, _ = lint(text)
        assert [f["line"] for f in findings if f["rule"] == "semicolon"] == lines, (text, findings)
    # the end of a quoted fence in a list item does not join the next line to the item
    findings, _ = lint("- Item\n  > ```\n  > code\nProse and")
    assert findings == [], findings
    # a tab is indent up to the next tab stop of 4, from its real column, also after ">"
    for text, line in (("\t```\n\tx = 1\n\t```\n\nProse; here.", 5),
                       ("```\nx\n\t```\ny; z\n```\n\nProse; here.", 7),
                       ("> ```\n> x\n>\t```\n> Use a; b.", 4),
                       ("> ```\n> x\n>  \t```\n> Use a; b.", 4),
                       (">\t> ```\n>\t> x; y\n>\t> ```\n\nProse; here.", 5),
                       ("- Item\n  ```\n\t```\n\nProse; here.", 5)):
        findings, _ = lint(text)
        assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", line)], (text, findings)
    # a tab-indented fence stays in its list item
    findings, _ = lint("- Run the build and\n\t```\n\tmake\n\t```\n  check the log.")
    assert findings == [], findings
    # a ">" line in an HTML block is text, not a quoted fence. A blank line ends a
    # block that starts with a tag, and a quoted fence after it is a fence.
    for text, lines in (("<div>\n> ```\n> Prose; here.\n> ```\n</div>", [3]),
                        ("<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [3]),
                        ("<!--\n> ```\n> Prose; here.\n> ```\n-->", [3]),
                        ("<div>\n\n> ```\n> x; y\n> ```\n\nProse; here.", [7]),
                        ("<details>\n\n> ```\n> a; b\n> ```\n\n</details>\n\nProse; here.", [9]),
                        ("<pre>\n> ```\n> Prose; here.\n> ```\n</pre>", [3]),
                        ("<?php\n> ```\n> Prose; here.\n> ```\n?>", [3]),
                        ("<![CDATA[\n> ```\n> Prose; here.\n> ```\n]]>", [3]),
                        # inline HTML is no HTML block: the quoted fence after it is a fence
                        ("<span>Label</span>\n> ```\n> a; b\n> ```", []),
                        ("<kbd>Enter</kbd> starts the job.\n> ```\n> a; b\n> ```", []),
                        ("Text.\n<custom>\n> ```\n> a; b\n> ```", [])):
        findings, _ = lint(text)
        assert [f["line"] for f in findings if f["rule"] == "semicolon"] == lines, (text, findings)
    # a fence at column 0 ends a list item
    findings, _ = lint("- Do this and\n```\nx\n```\n  done")
    assert [(f["rule"], f["line"]) for f in findings] == [("dangling-conjunction", 1)], findings
    # a quoted fence also ends on a line with fewer quote levels that is not blank
    for text, line in (("> ```\n> x\nProse; here.", 3), ("> > ```\n> x; y", 2)):
        findings, _ = lint(text)
        assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", line)], (text, findings)
    # a closing fence up to three columns deeper than the opening fence closes it
    findings, _ = lint("```\nx; y\n   ```\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 5)], findings
    # a tilde fence opens with a backtick in its info string
    findings, _ = lint("~~~ a`b\nx; y\n~~~\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 5)], findings
    # an alert marker after a fence in the same quote is text, as GitHub shows it
    body = " ".join(["word"] * 25) + "."
    findings, _ = lint(f"> ```\n> x\n> ```\n> [!NOTE]\n> {body}")
    assert [f["rule"] for f in findings] == ["long-sentence"], findings
    # a quoted fence after a list item does not join the item
    findings, _ = lint("- Do this and\n\n> ```\n> code\n> ```\n  done")
    assert [f["rule"] for f in findings] == ["dangling-conjunction"], findings
    # all supported list markers, case variants, and trailing whitespace
    findings, _ = lint(
        "- Confirm the target and\n"
        "* Record the result OR  \n"
        "+ Close the panel\n"
        "1. Start the task and\n"
        "2) Stop the task OR"
    )
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 4, dangling
    assert [f["line"] for f in dangling] == [1, 2, 4, 5], dangling
    assert [f["col"] for f in dangling] == [1, 1, 1, 1], dangling
    assert all(f["level"] == "advisory-free" for f in dangling), dangling

    # valid continuation lines and standalone four-space code are ignored
    findings, _ = lint("  - Confirm the target and\n    record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Confirm the target\n  and")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["line"] == 2, dangling
    assert dangling[0]["col"] == 3, dangling
    findings, _ = lint("    - code and")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("> - Confirm the target and\n> - Record the result or")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Do this and\n~~~\ncode and\n~~~")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["line"] == 1, dangling
    findings, _ = lint("```text\n- code and\n```")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)

    # one- and three-space markers and ordered continuation width
    findings, _ = lint(" - Start the task and\n   record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("-  Start the task and\n   record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("-\tStart the task and")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("   - Start the task and", filename="fixture.md")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["col"] == 4, dangling
    assert dangling[0]["file"] == "fixture.md"
    assert dangling[0]["match"].endswith("and")
    assert "Complete the item" in dangling[0]["message"]
    findings, _ = lint("100. Start the task and\n  unrelated text")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1, dangling
    findings, _ = lint("- Start the task and.\n- Stop the task or,")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Start the task and\n\n  record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Parent item and\n  - Nested item or")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert [f["line"] for f in dangling] == [1, 2], dangling

    # ordinary prose, inline code, and fenced code are ignored
    findings, _ = lint("The process may include steps and")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Use `and` as a label")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Combine `left` and `right`")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings), findings
    findings, _ = lint("~~~\n- code and\n~~~")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint(("word " * 30).strip() + ".")
    assert any(f["rule"] == "long-sentence" for f in findings)
    # Markdown table syntax is layout, not prose. Each cell stays lintable.
    short_cell = " ".join(f"term{number}" for number in range(1, 25)) + "."
    for table in (
            "| Label | Detail |\n"
            "| --- | --- |\n"
            f"| Clear | {short_cell} |",
            "Label | Detail\n"
            "--- | ---\n"
            f"Clear | {short_cell}"):
        findings, words_total = lint(table)
        assert not any(f["rule"] == "long-sentence" for f in findings), findings
        assert words_total == 27, words_total
    long_cell = " ".join(f"term{number}" for number in range(1, 27)) + "."
    findings, _ = lint(
        "| Label | Detail |\n"
        "| --- | --- |\n"
        f"| Clear | {long_cell} |"
    )
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert len(long_sentences) == 1, long_sentences
    assert long_sentences[0]["match"] == "26 words", long_sentences
    # synonym rotation: second member flagged, first named as the keeper
    findings, _ = lint("Check the config file. Then verify the output. Verify twice.")
    rot = [f for f in findings if f["rule"] == "synonym-rotation"]
    assert len(rot) == 1 and "'verify' and 'check'" in rot[0]["message"], rot
    # single consistent term: no flag
    findings, _ = lint("Check the config. Check the output.")
    assert not any(f["rule"] == "synonym-rotation" for f in findings)
    # per-file labels
    findings, _ = lint("a; b", filename="x.md")
    assert findings[0]["file"] == "x.md"
    # inline code is masked, not deleted, so columns match the source
    findings, _ = lint("Run `make all` then spin up the node.")
    phrasal = [f for f in findings if f["rule"] == "phrasal-verb"]
    assert len(phrasal) == 1 and phrasal[0]["col"] == 21, phrasal
    # a sentence ends after closing quotes and brackets
    twenty = " ".join(["word"] * 20)
    findings, _ = lint(f'He asked "{twenty}?" Then {twenty} ended. (It {twenty}.) Next.')
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # abbreviations do not end a sentence
    findings, _ = lint(f"Use a tool, e.g. the {twenty} linter here now.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"Compare A vs. B in the {twenty} test.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # a sentence wrapped across lines is counted once, at its start
    findings, _ = lint(f"Intro text here.\nThe {twenty}\nwrapped tail words go here.")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert len(long_sentences) == 1, long_sentences
    assert (long_sentences[0]["line"], long_sentences[0]["col"]) == (2, 1), long_sentences
    findings, _ = lint(f"- Item {twenty}\n  continued in the same item.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # blank lines, headings, rules, list items, and quotes end a prose block
    for sep in ("\n\n", "\n# Heading\n", "\n---\n", "\n- ", "\n> "):
        findings, _ = lint(f"First {twenty} line{sep}Second {twenty} line.")
        assert not any(f["rule"] == "long-sentence" for f in findings), (sep, findings)
    # a GitHub alert marker on the first line of a quote is not a word of the body
    body = " ".join(["word"] * 25) + "."
    for alert in ("> [!NOTE]", "> [!tip]", ">[!Warning]", ">  [!CAUTION]  "):
        findings, _ = lint(f"{alert}\n> {body}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (alert, findings)
    for text in (f"Text.\n\n> [!NOTE]\n> {body}", f"> Text.\n~~~\ncode\n~~~\n> [!NOTE]\n> {body}"):
        findings, _ = lint(text)
        assert not any(f["rule"] == "long-sentence" for f in findings), (text, findings)
    # Inside HTML containers the marker is text: marker plus body is 26 words.
    for opening, closing in (("<details>", "</details>"),
                             ('<DIV class="note">', "</DIV>"),
                             ("<section><details>", "</details></section>")):
        findings, _ = lint(f"{opening}\n\n> [!NOTE]\n> {body}\n\n{closing}")
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (opening, findings)
        findings, _ = lint(f"{opening}\n{closing}\n\n> [!NOTE]\n> {body}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (opening, findings)
    findings, _ = lint(f"> [!NOTE]\n> {body}")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # An inner close or a fenced closing tag must not close the outer container.
    for content in ("<details>\n<div>\n</div>",
                    "<details>\n~~~\n</details>\n~~~"):
        findings, _ = lint(f"{content}\n\n> [!NOTE]\n> {body}\n\n</details>")
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (content, findings)
    # Fenced, commented, inline, void, and self-closing tags do not open containers.
    for content in ("```html\n<details>\n```", "<!-- <details> -->",
                    "<span>Text.</span>", "<hr>", "<div />",
                    "<details></details>", "</details>"):
        findings, _ = lint(f"{content}\n\n> [!NOTE]\n> {body}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (content, findings)
    # GitHub shows these markers as text, so they stay words. GitHub shows the
    # last two as alerts, but no blank line or fence proves that a quote starts.
    for text in (f"> [!FOO]\n> {body}", f"> [!NOTE] {body}", f"> Intro.\n> [!NOTE]\n> {body}",
                 f"> > [!NOTE]\n> > {body}", f"> Intro.\ncontinuation.\n> [!NOTE]\n> {body}",
                 f"- Item.\n\n  > [!NOTE]\n  > {body}",
                 f"Text.\n> [!NOTE]\n> {body}", f"   > [!NOTE]\n   > {body}"):
        findings, _ = lint(text)
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (text, long_sentences)
    # a bold or italic lead sentence ends at its closing emphasis marker
    findings, _ = lint(f"**Lead.** The {twenty} more words here now.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"_Note._ The {twenty} more words here now.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"See **e.g.** the {twenty} linter here now.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # a dotted abbreviation ends a sentence before a capitalized word
    findings, _ = lint(f"The team shipped it in the U.S. Then {twenty} today.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # nested list items, quoted list items, and HTML lines end a prose block
    for text in (f"- First item\n    - First {twenty} line\n      - Second {twenty} line",
                 f"> - First {twenty} line\n> - Second {twenty} line",
                 f"<!-- First {twenty} line -->\nSecond {twenty} line.",
                 f"> First {twenty} line.\n>\n> Second {twenty} line."):
        findings, _ = lint(text)
        assert not any(f["rule"] == "long-sentence" for f in findings), (text, findings)
    # a blockquote prefix is not a word in a wrapped quoted sentence
    findings, _ = lint("> " + "\n> ".join(["word word word word word"] * 5) + ".")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # a list marker is not a word either, in every marker style
    twenty_five = " ".join(f"term{number}" for number in range(1, 26)) + "."
    for marker in ("-", "*", "+", "1.", "1)", "  -", "> -"):
        findings, _ = lint(f"{marker} {twenty_five}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (marker, findings)
    findings, _ = lint(f"- term0 {twenty_five}")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert [(f["match"], f["col"]) for f in long_sentences] == [("26 words", 3)], long_sentences
    # a code span at the line start does not turn the next token into a list marker
    findings, _ = lint(f"`label` 1) {twenty_five}")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert [f["match"] for f in long_sentences] == ["26 words"], long_sentences
    # bare punctuation is not a word: code-span separators and spaced dashes
    for separator in (", ", " ", " / "):
        names = separator.join(f"`a{number}`" for number in range(30))
        findings, _ = lint(f"The adapters are {names}.")
        assert not any(f["rule"] == "long-sentence" for f in findings), (separator, findings)
    findings, _ = lint(" ".join(f"term{number}" for number in range(1, 25)) + " — term25.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"Use `make` — {twenty_five}")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert [f["match"] for f in long_sentences] == ["26 words"], long_sentences
    # a long block stays linear: one short sentence per line, no blank lines
    findings, _ = lint("The agent read the log.\n" * 20000)
    assert not any(f["rule"] == "long-sentence" for f in findings)
    # flags may appear between file paths
    with tempfile.TemporaryDirectory() as tmp:
        paths = [os.path.join(tmp, name) for name in ("a.md", "b.md")]
        for path in paths:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("Short line here.\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert main([paths[0], "--json", paths[1]]) == 0
        assert json.loads(out.getvalue())["words"] == 6, out.getvalue()
    # command-line parsing rejects typos and bad values
    for bad in (["--basline", "3"], ["--baseline"], ["--baseline", "x"],
                ["--baseline", "-1"], ["--disable", "passive"], ["--base", "3"]):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                main(bad)
        except SystemExit as e:
            assert e.code == 2, (bad, e.code)
        else:
            raise AssertionError(bad)
    assert _rule_list("passive-voice,present-perfect") == {"passive-voice", "present-perfect"}
    print("selftest OK")


RULE_IDS = {rule_id for rule_id, *_ in RULES} | {
    "long-sentence", "synonym-rotation", "dangling-conjunction"}


def _rule_list(value):
    rules = {r for r in value.split(",") if r}
    unknown = rules - RULE_IDS
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown rule(s): {', '.join(sorted(unknown))}. "
            f"Known rules: {', '.join(sorted(RULE_IDS))}")
    return rules


def _non_negative_int(value):
    try:
        n = int(value)
    except ValueError:
        n = -1
    if n < 0:
        raise argparse.ArgumentTypeError(f"expected a non-negative integer, got {value!r}")
    return n


def main(argv):
    parser = argparse.ArgumentParser(
        prog="ste-lint.py", allow_abbrev=False,
        description="Deterministic linter for the structural STE rules. "
                    "Reads stdin when no FILE is given.")
    parser.add_argument("paths", nargs="*", metavar="FILE")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--baseline", type=_non_negative_int, default=0, metavar="N",
                        help="pass unless hard violations exceed N (default 0)")
    parser.add_argument("--disable", type=_rule_list, default=set(), metavar="RULES",
                        help="comma-separated rule IDs to silence")
    parser.add_argument("--selftest", action="store_true", help="run the built-in tests")
    # intermixed parsing keeps flags valid between file paths
    args = parser.parse_intermixed_args(argv)
    if args.selftest:
        selftest()
        return 0
    as_json, baseline, disabled, paths = args.json, args.baseline, args.disable, args.paths

    findings, words_total = [], 0
    if paths:
        for p in paths:
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError as e:
                parser.error(f"cannot read {p}: {e.strerror}")
            f, w = lint(text, filename=p)
            findings.extend(f)
            words_total += w
    else:
        findings, words_total = lint(sys.stdin.read())

    findings = [f for f in findings if f["rule"] not in disabled]
    hard_count = sum(1 for f in findings if f["level"] == "advisory-free")
    report(findings, words_total, as_json, hard_count, baseline)
    return 1 if hard_count > baseline else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
