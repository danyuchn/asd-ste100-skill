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
import html.entities
import io
import itertools
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
# Up to two words may stand between the modal and "have": "may not",
# "might already", "could not possibly", "may very well".
MODAL_PERFECT_PREFIX = re.compile(
    r"\b(?:(?:may|might|could|should|would|must|can|will|shall)(?:n['’]t)?"
    r"|cannot|can['’]t|won['’]t|shan['’]t)"
    r"(?:\s+(?:not|already|also|ever|even|just|never|still|very|well|\w+ly)){0,2}\s+$",
    re.I,
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
BACKTICK_RUN = re.compile(r"`+")
# A list item start at any indent, to find the content indent of its item.
LIST_ITEM_INDENT = re.compile(r"^( *)([-*+]|[0-9]+[.)])( +|$)")
# Markup that is not prose: character references (&nbsp; &#39; &#x2192;) and
# autolinks (<https://...>). Inline link destinations ("](url") are found by
# _link_destination_end. A reference is markup only when GitHub reads it as one.
CHAR_REF = re.compile(r"&(?:([A-Za-z][A-Za-z0-9]{1,31})|#([0-9]{1,7})|#[xX]([0-9A-Fa-f]{1,6}));")
LINK_OPEN = re.compile(r"\]\(")
# A list item or a fence that can interrupt a paragraph: a bullet or "1." with text.
PARAGRAPH_INTERRUPT = re.compile(r" {0,3}(?:[-+*][ \t]+\S|1[.)][ \t]+\S|`{3,}|~{3,})")
AUTOLINK = re.compile(r"<[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\s]*>")
# CommonMark 6.3 lets an implementation limit the nesting of parentheses in a
# link destination. The limit keeps the scan of a long line linear.
MAX_LINK_PARENS = 32
ASCII_PUNCTUATION = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
LIST_ITEM_START = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>[-*+]|[0-9]+[.)])(?P<gap> +)(?P<body>.*)$"
)
CONJUNCTION_END = re.compile(r"\b(?:and|or)\s*$", re.I)
TABLE_SEPARATOR_CELL = re.compile(r"^:?-+:?$")
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


def _is_leaf_line(line):
    """True when LINE is a heading, thematic break, HTML line, or fence delimiter.

    No paragraph text continues such a line.
    """
    return bool(STANDALONE_LINE.match(_strip_quotes(line)[1]) or _fence_step(None, line)[0])


def _breaks_paragraph(prev, line):
    """True when LINE cannot continue the paragraph that PREV is in.

    A code span ends there too (CommonMark 6.1): a blank or quote-only line,
    a list item, a heading, a thematic break, a fence, or another quote depth.
    """
    depth, rest = _strip_quotes(line)
    return (not rest.strip() or bool(ANY_LIST_ITEM.match(rest))
            or depth != _strip_quotes(prev)[0]
            or _is_leaf_line(prev) or _is_leaf_line(line))


def _closes_later(run, lines, start, prev):
    """True when a backtick run of length RUN is in LINES[START:] in the paragraph of PREV."""
    # ponytail: scans to the paragraph end for each unclosed run, so a single
    # paragraph of N lines with N unclosed runs costs O(N^2). Memoize per length if that shows up.
    for index in range(start, len(lines)):
        line = lines[index]
        if _breaks_paragraph(prev, line):
            return False
        if any(len(m.group()) == run for m in BACKTICK_RUN.finditer(line)):
            return True
        prev = line
    return False


def _mask_code_spans(line, open_run, lines, next_index=0, depth=0, skip=0, carry=None):
    """Blank the code spans in LINE, also a span that wraps across lines.

    OPEN_RUN is the backtick run length of a span still open from an earlier
    line, or 0. LINES[NEXT_INDEX:] are the lines after LINE. As in CommonMark 6.1, a
    span ends at the next run of the same length, and a run that no later run
    in the paragraph closes is literal text. Outside code spans, fill inline
    link destinations with underscores. What starts first wins: a code span
    that opens before "](" hides the link, and a backtick in a link is text.
    DEPTH is the quote depth of the paragraph that LINE is in, or None when no
    paragraph goes on after LINE, so a link must close in it. SKIP is where a
    link from an earlier line ends in LINE. When a link goes on in a later
    line, CARRY gets [lines ahead, column after its ")"]. Return (masked line,
    open run).
    """
    masked = list(line)
    start = 0 if open_run else None
    runs = list(BACKTICK_RUN.finditer(line))
    opens = [m.end() for m in LINK_OPEN.finditer(line)]
    k = 0
    done = skip  # the end of the last code span or link

    def mask_links(limit):
        # Fill the destinations after the "](" marks before LIMIT.
        nonlocal k, done
        while k < len(opens) and opens[k] <= limit:
            pos = opens[k]
            k += 1
            if pos - 2 < done:
                continue
            link = _link_destination_end(line, pos, itertools.islice(lines, next_index, None), depth)
            if link is not None and link[0] > pos:
                masked[pos:link[0]] = "_" * (link[0] - pos)
                done = link[1]
                if carry is not None and link[2]:
                    carry[:] = link[2]

    for i, run in enumerate(runs):
        n = len(run.group())
        if start is not None:
            if n == open_run:
                masked[start:run.end()] = " " * (run.end() - start)
                start, open_run = None, 0
                done = run.end()
            continue
        mask_links(run.start())
        if run.start() < done:
            continue  # a backtick in a link is text
        if (any(len(r.group()) == n for r in runs[i + 1:])
                or _closes_later(n, lines, next_index, line)):
            start, open_run = run.start(), n
    if start is not None:
        masked[start:] = " " * (len(line) - start)
    else:
        mask_links(len(line))
    return "".join(masked), open_run


def _char_ref_is_markup(match):
    """True when the character reference MATCH renders as one character.

    A named reference counts only when its name is in the HTML5 list. A
    reference that renders as a semicolon is prose: GitHub shows a semicolon.
    """
    name, decimal, hexadecimal = match.groups()
    if name is not None:
        return name + ";" in html.entities.html5 and name != "semi"
    value = int(decimal) if decimal is not None else int(hexadecimal, 16)
    return value != ord(";")


def _paragraph_lines(later_lines, depth):
    """Yield (text, column, lines ahead) for the lines that continue the paragraph.

    TEXT is the line without its quote prefix, which ends at COLUMN.

    DEPTH is the quote depth of the paragraph, or None when no paragraph goes
    on. A blank line, a deeper quote and a line that starts a block end the
    paragraph (CommonMark 4.1 to 4.6, 5.1 and 5.2). A line with fewer ">" is a
    lazy line and continues it.
    """
    if depth is None:
        return
    for ahead, line in enumerate(later_lines, 1):
        levels, rest = _strip_quotes(line)
        if (levels > depth or not rest.strip() or NO_PARAGRAPH.match(rest)
                or SETEXT_UNDERLINE.match(rest) or PARAGRAPH_INTERRUPT.match(rest)
                or any(start.match(rest) for start, _ in HTML_BLOCK_KINDS)):
            return
        yield rest, len(line) - len(rest), ahead


def _skip_link_gap(item, pos, rest):
    """Skip spaces and tabs from POS, with at most one line ending.

    ITEM is (text, column, lines ahead), and REST yields the next items of the
    paragraph. Return (item, pos, crossed), or None when the paragraph ends.
    """
    while pos < len(item[0]) and item[0][pos] in " \t":
        pos += 1
    if pos < len(item[0]):
        return item, pos, False
    item = next(rest, None)
    if item is None:
        return None
    pos = 0
    while pos < len(item[0]) and item[0][pos] in " \t":
        pos += 1
    return item, pos, True


def _skip_link_title(item, pos, rest):
    """Return (item, pos) after a link title that starts at POS, or None.

    ITEM is (text, column, lines ahead). The title can go on in the next lines
    of the paragraph (REST), but it must close before the paragraph ends.
    """
    line = item[0]
    closer = {'"': '"', "'": "'", "(": ")"}[line[pos]]
    pos += 1
    while True:
        while pos < len(line):
            if line[pos] == "\\" and pos + 1 < len(line) and line[pos + 1] in ASCII_PUNCTUATION:
                pos += 2
                continue
            if line[pos] == closer:
                return item, pos + 1
            if closer == ")" and line[pos] == "(":
                return None
            pos += 1
        item, pos = next(rest, None), 0
        if item is None:
            return None
        line = item[0]


def _link_destination_end(text, start, later_lines=(), depth=None):
    """Return (destination end, link end, carry) for the destination at START, or None.

    START is after "](". CommonMark 6.3: the destination is in <...>, or it has
    no space or control character and its parentheses are balanced. An
    optional title and ")" must follow, in the same paragraph. LATER_LINES are
    the lines after TEXT, and DEPTH is the quote depth of the paragraph (see
    _paragraph_lines). Each gap of spaces and tabs may hold one line ending,
    and the title may span lines. The link end is after ")" when the link
    closes in TEXT, else the end of TEXT, and CARRY is then (lines ahead,
    column after ")") of the line where it closes, else None.
    """
    pos = start
    if pos < len(text) and text[pos] == "<":
        pos += 1
        while pos < len(text) and text[pos] not in "<>":
            pos += 2 if text[pos] == "\\" and pos + 1 < len(text) else 1
        if pos >= len(text) or text[pos] != ">":
            return None
        end = pos + 1
    else:
        parens = 0
        while pos < len(text):
            char = text[pos]
            if char == "\\" and pos + 1 < len(text) and text[pos + 1] in ASCII_PUNCTUATION:
                pos += 2
                continue
            if char <= " " or char == "\x7f":
                break
            if char == "(":
                parens += 1
                if parens > MAX_LINK_PARENS:
                    return None
            elif char == ")":
                if parens == 0:
                    break
                parens -= 1
            pos += 1
        if parens:
            return None
        end = pos
    rest = _paragraph_lines(later_lines, depth)
    gap = _skip_link_gap((text, 0, 0), end, rest)
    if gap is None:
        return None
    item, pos, crossed = gap
    if (crossed or pos > end) and item[0][pos] in "\"'(":
        title = _skip_link_title(item, pos, rest)
        if title is None:
            return None
        gap = _skip_link_gap(*title, rest)
        if gap is None:
            return None
        item, pos, _ = gap
    if item[0][pos] != ")":
        return None
    if item[2] == 0:
        return end, pos + 1, None
    return end, len(text), (item[2], item[1] + pos + 1)


def _mask_non_prose(text):
    """Blank code spans, then fill character references and autolinks.

    The fill is underscores, not spaces, so a token stays one token and word
    counts do not change. An underscore is not a word character for _count_words.
    Link destinations are filled by _mask_code_spans.
    """
    text = _mask_inline_code(text)
    out = []
    pos = done = 0
    while pos < len(text):
        end = None
        if text[pos] == "&":
            ref = CHAR_REF.match(text, pos)
            if ref and _char_ref_is_markup(ref):
                end = ref.end()
        if end is None and text[pos] == "<":
            link = AUTOLINK.match(text, pos)
            if link:
                end = link.end()
        if end is None:
            pos += 1
            continue
        out.append(text[done:pos])
        out.append("_" * (end - pos))
        pos = done = end
    out.append(text[done:])
    return "".join(out)


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
# Type 7: one complete open or closing tag alone on its line (CommonMark 6.6 grammar).
# It cannot interrupt a paragraph.
_ATTRIBUTE = (r"\s+[A-Za-z_:][A-Za-z0-9_.:-]*"
              r"(?:\s*=\s*(?:[^\s\"'=<>`]+|'[^']*'|\"[^\"]*\"))?")
# The names of type 1 (pre, script, style, textarea) never start a type 7 block,
# as an open tag or as a closing tag. A custom name such as pre-x is no type 1 name.
_TYPE1_NAME = r"(?!(?i:pre|script|style|textarea)(?![A-Za-z0-9-]))"
HTML_TYPE7 = re.compile(
    rf"^ {{0,3}}(?:<{_TYPE1_NAME}[A-Za-z][A-Za-z0-9-]*(?:{_ATTRIBUTE})*\s*/?>"
    rf"|</{_TYPE1_NAME}[A-Za-z][A-Za-z0-9-]*\s*>)\s*$")
# Lines that end a paragraph and are no paragraph line, after the quote prefix: an ATX
# heading and a thematic break of one repeated character. A quote line with no text
# also ends a paragraph.
NO_PARAGRAPH = re.compile(
    r"^ {0,3}(?:#{1,6}(?:\s|$)|(?:-[ \t]*){3,}$|(?:\*[ \t]*){3,}$|(?:_[ \t]*){3,}$)")
# A setext underline. It ends a paragraph only when a paragraph is open at the same
# quote depth. Else it is text, also as a lazy line after a quote (CommonMark 4.3).
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")


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


def _is_list_continuation(line, content_indent):
    if not line.strip():
        return True
    if LIST_ITEM_START.match(line):
        return False
    return len(line[:len(line) - len(line.lstrip(" \t"))].expandtabs(4)) >= content_indent


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


# A line of YAML front matter: a key, a list item, an indented line, or a comment.
# A key is quoted, or a plain word that starts with no YAML indicator; ": "
# or ":" at the end of the line ends it. A plain key with a space is valid
# YAML, but prose such as "Step 1: run it" looks the same, so it is Markdown.
_YAML_KEY = (r"""(?:"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^\s#'"\[\]{},&*!|>%@`-]\S*?)"""
             r"[ \t]*:(?:[ \t]|$)")
FRONT_MATTER_KEY = re.compile(_YAML_KEY)
FRONT_MATTER_LINE = re.compile(_YAML_KEY + r"|-(?:[ \t]|$)|[ \t]+\S|#")
DESCRIPTION_KEY = re.compile(r"description[ \t]*:(?:[ \t]+|$)")
# A block scalar indicator ("|", ">-", "|2+"), with an optional comment.
BLOCK_SCALAR = re.compile(r"[|>][1-9+-]{0,2}(?:[ \t]+#.*)?")
# A YAML comment in a plain scalar: "#" at the start or after a space or tab.
YAML_COMMENT = re.compile(r"(?:^|[ \t])#")


def _closing_quote(text, quote):
    """Return the index of the QUOTE that closes a quoted YAML scalar in TEXT, or None.

    In single quotes, '' is a quote. In double quotes, a backslash escapes the
    next character.
    """
    pos = 0
    while pos < len(text):
        if quote == '"' and text[pos] == "\\":
            pos += 2
            continue
        if text[pos] == quote:
            if quote == "'" and text[pos + 1:pos + 2] == "'":
                pos += 2
                continue
            return pos
        pos += 1
    return None


def _scalar_pieces(value, parts):
    """Return the prose pieces of a YAML scalar as (line index, column, text).

    VALUE is the text after the key. PARTS are the lines of the scalar with
    their line index and the column of their text, the key line first when
    VALUE is not empty. A block scalar ("|", ">-") keeps each later line up to
    one with less indent than its first, also a "#". A quoted scalar ends at
    its closing quote. A plain scalar ends at a comment. A comment after the
    scalar is not prose.
    """
    pieces = []
    if BLOCK_SCALAR.fullmatch(value):
        # The first line sets the indent. A line with less indent, such as a
        # comment, ends the scalar.
        for piece in parts[1:]:
            if piece[1] < parts[1][1]:
                break
            pieces.append(piece)
    elif value[:1] in ("'", '"'):
        index, column, text = parts[0]
        parts = [(index, column + 1, text[1:])] + parts[1:]
        for index, column, text in parts:
            close = _closing_quote(text, value[0])
            pieces.append((index, column, text if close is None else text[:close]))
            if close is not None:
                break
    else:
        for index, column, text in parts:
            comment = YAML_COMMENT.search(text)
            pieces.append((index, column, text if comment is None else text[:comment.start()]))
            if comment is not None:
                break
    return [piece for piece in pieces if piece[2].strip()]


def _front_matter(text):
    """Find a leading YAML front-matter block.

    Return (text, description): TEXT with the block blanked, so line numbers
    stay true, and the value of its "description:" key as (line index,
    column, text) pieces. The block counts only when its first line that is
    not a comment is a key, and every line is a key, a list item, an indented
    line, a comment or a blank line. Else it is Markdown: a thematic break,
    prose and a second thematic break. Only the description is prose, because
    agents act on it.
    """
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return text, []
    for end in range(1, len(lines)):
        if lines[end].rstrip() == "---":
            break
    else:
        return text, []
    body = [line for line in lines[1:end] if line.strip()]
    content = [line for line in body if not line.startswith("#")]
    if (body and (not content or not FRONT_MATTER_KEY.match(content[0]))
            or not all(FRONT_MATTER_LINE.match(line) for line in body)):
        return text, []
    pieces = []
    for index in range(1, end):
        key = DESCRIPTION_KEY.match(lines[index])
        if key:
            break
    else:
        index = end
    if index < end:
        value = lines[index][key.end():].rstrip()
        parts = [(index, key.end(), value)] if value else []
        for later in range(index + 1, end):
            line = lines[later]
            if line.strip() and not line[0] in " \t":
                break
            lead = len(line) - len(line.lstrip(" \t"))
            if line[lead:].rstrip():
                parts.append((later, lead, line[lead:].rstrip()))
        pieces = _scalar_pieces(value, parts)
    return "\n" * (end + 1) + "\n".join(lines[end + 1:]), pieces


def lint(text, filename="<stdin>"):
    text, description = _front_matter(text)
    findings = []
    words_total = 0
    fence = None
    html_block = None
    html_depth = 0
    in_paragraph = False
    # content indent of the open list item, so its indented lines are not code
    list_indent = 0
    # backtick run length of a code span that is open across lines, or 0
    open_span = 0
    paragraph_depth = 0
    # (line number, column) where a link from an earlier line ends, or None
    link_end = None
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

    def check(lineno, segment, source_column, line, skip, is_table):
        nonlocal words_total
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
        if line[skip:].strip():
            block.append((lineno, source_column + skip, line[skip:]))

    # The description in the front matter is one paragraph of prose.
    span = 0
    values = [piece[2] for piece in description]
    for position, (index, column, value) in enumerate(description):
        masked, span = _mask_code_spans(value, span, values, position + 1)
        check(index + 1, value, column, _mask_non_prose(masked), 0, False)
    flush()

    for lineno, raw_line in enumerate(lines, 1):
        was_paragraph = in_paragraph
        if open_span and _breaks_paragraph(lines[lineno - 2], raw_line):
            open_span = 0
        if _fence_ends_with_quote(fence, raw_line):
            # The quote that holds the fence ended: judge this line as any other line.
            fence = None
        in_html = False
        if fence is None:
            # An HTML block can sit in a block quote. It ends when its quote ends. An
            # open block strips only its own ">" levels: a deeper ">" is its text.
            if html_block is not None:
                line_depth, line_unquoted = _strip_quotes(raw_line.expandtabs(4), html_depth)
                if line_depth < html_depth:
                    html_block = None
            if html_block is None:
                line_depth, line_unquoted = _strip_quotes(raw_line.expandtabs(4))
            # A deeper quote starts a block quote, which a paragraph outside it does not continue.
            continues = in_paragraph and line_depth <= paragraph_depth
            was_html = html_block is not None
            in_html, html_block = _html_block_step(html_block, line_unquoted, continues)
            if in_html and not was_html:
                html_depth = line_depth
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
        if rest.strip() and not in_html:
            if indent >= list_indent + 4:
                if not was_paragraph:
                    in_paragraph = False
                    continue
            else:
                # An item line sets the content indent also after a text line or
                # in a tight list. A lazy line does not end the item.
                item = LIST_ITEM_INDENT.match(rest)
                if item:
                    list_indent = len(item.group(0)) if item.group(3) else len(item.group(0)) + 1
                elif indent < list_indent and not was_paragraph:
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
            if in_html:
                # an HTML block has no code spans and no Markdown links
                line = _mask_non_prose(segment)
            elif is_table:
                # a table cell holds its own spans and links
                line = _mask_non_prose(_mask_code_spans(segment, 0, ())[0])
            else:
                skip = 0
                if link_end and link_end[0] > lineno:
                    skip = len(segment)  # the whole line is in the title of a link
                elif link_end and link_end[0] == lineno:
                    skip = link_end[1]
                carry = []
                masked, open_span = _mask_code_spans(segment, open_span, lines, lineno,
                                                     paragraph_depth if in_paragraph else None,
                                                     skip, carry)
                if carry:
                    link_end = (lineno + carry[0], carry[1])
                elif link_end and link_end[0] <= lineno:
                    link_end = None
                line = _mask_non_prose(masked)
            # the blockquote prefix and the list marker are markup, not words in the sentence
            skip = quote.end() if quote and not is_table else 0
            marker = None if is_table else ANY_LIST_ITEM.match(segment[skip:])
            if marker:
                skip += marker.end()
            check(lineno, segment, source_column, line, skip, is_table)
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
    findings, _ = lint("It might already have finished. It could not possibly have run. "
                       "It may never have started. It should probably have stopped.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    findings, _ = lint("It cannot have run. It won't have finished. It can't have stopped. "
                       "It may well have failed. It may very well have failed.\n\n"
                       "The request may\nhave failed.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    # a modal in an earlier paragraph does not protect the next one
    findings, _ = lint("It may\n\nhave failed.")
    assert sum(f["rule"] == "present-perfect" for f in findings) == 1, findings
    # an adverb without a modal is not a hedge
    findings, _ = lint("The task already has run. They probably have finished.")
    assert sum(f["rule"] == "present-perfect" for f in findings) == 2, findings
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
                        ("Text.\n<custom>\n> ```\n> a; b\n> ```", []),
                        # a type 7 tag after a heading or a fence starts a block
                        ("# Title\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [4]),
                        ("```\nx\n```\n<img src=\"a.png\">\n> ```\n> Prose; here.\n> ```", [6]),
                        # attribute values may hold "<" and ">", an invalid attribute is no tag
                        ('<span title="a > b">\n> ```\n> Prose; here.\n> ```', [3]),
                        ("<custom a=>\n> ```\n> a; b\n> ```", []),
                        # a setext underline, an empty quote line and a thematic break of one
                        # character end a paragraph, so a type 7 tag after them starts a block
                        ("Title\n=====\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [5]),
                        ("> Quote.\n>\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [5]),
                        ("-*-\n<custom>\n> ```\n> a; b\n> ```", []),
                        ("Title\n-\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [5]),
                        ("> Quote.\n> >\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [5]),
                        # an underline with no paragraph, or as a lazy line, is text
                        ("Intro.\n\n==\n<custom>\n> ```\n> a; b\n> ```", []),
                        ("> Title\n===\n<custom>\n> ```\n> a; b\n> ```", []),
                        ("> > Title\n> lazy\n> ===\n<custom>\n> ```\n> a; b\n> ```", []),
                        # a quoted heading or thematic break is no paragraph line
                        ("> # Note\n> ===\n<custom>\n> ```\n> a; b\n> ```", []),
                        ("> Note\n> ***\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [5]),
                        # the line that ends a quoted fence can start an HTML block
                        ("> ```\n> x\n<custom>\n> ```\n> Prose; here.", [5]),
                        # a type 1 name is no type 7 tag
                        ("<pre/>\n> ```\n> a; b\n> ```", []),
                        ("</pre>\n> ```\n> a; b\n> ```", []),
                        ("<pre-x>\n> ```\n> Prose; here.\n> ```", [3]),
                        # no fence opens in an HTML block, also without ">"
                        ("<pre>\n```\nsample\n</pre>\n\nThe paragraph is here; it must be checked.", [6]),
                        ("<div>\n```\n\nProse; here.", [4]),
                        ("<DIV class=x>text\n> ```\n> Prose; here.\n> ```", [3])):
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
    findings, _ = lint("- Confirm the target and\n\trecord the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings), findings
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
    # GFM also accepts one-dash separators, one column, and ragged body rows.
    short_row = " ".join(f"term{number}" for number in range(1, 9))
    for table in (
            "| Label | Detail |\n|-|-|\n" + f"| {short_row} | {short_row} |\n" * 5,
            "| Label |\n| --- |\n" + f"| {short_row} |\n" * 8,
            "| Label | Detail |\n| --- | --- |\n| x |\n"
            + f"| {short_row} | {short_row} | extra |\n" * 2):
        findings, _ = lint(table)
        assert not any(f["rule"] == "long-sentence" for f in findings), (table, findings)
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
    # character references and link targets are markup, not prose
    findings, _ = lint("Press Ctrl&nbsp;C to stop &rarr; &#8594; &#x2192; now. "
                       "See [the docs](https://x.io/a;b) or <https://x.io/a;b>.")
    assert not any(f["rule"] == "semicolon" for f in findings), findings
    findings, _ = lint('See [a](https://x.io/a;b "Title") and [b](<a b;c>) and [c](a(b;c)).')
    assert not any(f["rule"] == "semicolon" for f in findings), findings
    # a reference GitHub does not read as one, or that renders ";", is prose
    for text in ("We closed the Q&As; then we left.", "Use &unknownentity; here.",
                 "Read this&#59; then stop.", "Read this&#x3b; then stop.", "Read&semi; this."):
        findings, _ = lint(text)
        assert [f["rule"] for f in findings] == ["semicolon"], (text, findings)
    # text in parentheses that is no link destination is prose
    findings, _ = lint("Read [this](seamless; now).")
    assert [f["rule"] for f in findings] == ["marketing-adjective", "semicolon"], findings
    for text in ("See [a](b;c d).", "See [a](b(c;d).", "See [a](<b;c).", "See [a](b;c \"t\" x)."):
        findings, _ = lint(text)
        assert [f["rule"] for f in findings] == ["semicolon"], (text, findings)
    # the link can go on in the next lines of its paragraph, and it must close there
    for text, cols in (("See [docs](https://x.io/a;b\n).", []),
                       ("See [a](b;c \"multi\nline title\") now.", []),
                       ("See [a](b;c\n\"title\") now.", []),
                       ("See [a](b;c (paren\ntitle)) now.", []),
                       ("> See [docs](https://x.io/a;b\n> ).", []),
                       ("See [docs](https://x.io/a;b\n\n).", [(1, 26)]),
                       ("See [a](b;c\n\n\"title\") now.", [(1, 10)]),
                       ("See [a](b;c\nnext line) now.", [(1, 10)]),
                       ("See [a](b(c);d \"oops).", [(1, 13)]),
                       ("See [a](b(c);d \"oops).\n\nNext; para.", [(1, 13), (3, 5)]),
                       ("See [a](b;c (paren (no)) now.", [(1, 10)]),
                       # a block that interrupts the paragraph ends the link
                       ("See [a](b;c \"x\n- y\") z.", [(1, 10)]),
                       ("See [a](b;c \"x\n# y\") z.", [(1, 10)]),
                       ("See [a](b;c \"x\n===\") z.", []),
                       ("See [a](b;c \"x\n===\n\") z.", [(1, 10)]),
                       ("See [a](b;c\n> )", [(1, 10)]),
                       ("> See [a](b;c\n)", []),
                       ("See [a](b;c \"x\n2. y\") z.", []),
                       # a backtick in a destination is text, and what starts first wins
                       ("See [a](https://x.io/a;b`c`tail).", []),
                       ("See [x](a`b;c) and `d` e; f.", [(1, 25)]),
                       ("Run `a [b](c;d` now.", []),
                       ("A `` [a](b;c `` d) e; f", [(1, 21)]),
                       ("| A | B |\n|-|-|\n| [a](b;c`d`e) | x |", []),
                       # a lazy line continues the quoted paragraph of the link
                       ("> First line\nSee [a](b;c\n> ) now.", []),
                       # a backtick in a title is text, a code span after the link is a span
                       ("See [a](b \"x`y\") and `z; w` now.", []),
                       # in a table cell the link starts first, and an HTML block has no links
                       ("| A | B |\n|-|-|\n| [a](b`c) d; e` f | x |", [(3, 13)]),
                       ("<div>\nSee [a](b;c) now.\n</div>", [(2, 10)]),
                       # a heading does not go on in the next line
                       ("# See [a](b;c\n) now.", [(1, 12)]),
                       # a title that goes on in the next line holds its backticks there too
                       ("See [a](b \"x\ny`z\") and `w; v` q.", []),
                       ("> See [a](b \"x\n> y\n> `z\") and `w; v` q.", []),
                       ("See [a](b \"x\ny\") a; `b` c", [(2, 6)])):
        findings, _ = lint(text)
        assert [(f["line"], f["col"]) for f in findings if f["rule"] == "semicolon"] == cols, (text, findings)
    findings, _ = lint("Press [stop](https://x.io); then wait. Use & ; here.")
    assert [f["col"] for f in findings if f["rule"] == "semicolon"] == [27, 46], findings
    # an indented code block is code, also in a quote and under a list item
    def semicolon_lines(text):
        return [f["line"] for f in lint(text)[0] if f["rule"] == "semicolon"]
    assert semicolon_lines("Intro text.\n\n    x = 1; y = 2\n\tz; w") == []
    assert semicolon_lines("> Intro.\n>\n>     x = 1; y = 2") == []
    assert semicolon_lines("- Item.\n\n      x = 1; y = 2") == []
    # it cannot interrupt a paragraph, and a list item's own indent is prose
    assert semicolon_lines("Intro text\n    goes on; here.") == [2]
    assert semicolon_lines("- Item.\n\n    More; text.") == [3]
    assert semicolon_lines("1. Item.\n\n   - Sub.\n\n     More; text.") == [5]
    # the list ends at a line with less indent
    assert semicolon_lines("- Item.\n\nText.\n\n    x; y") == []
    # a list item that follows a text line, or a nested item in a tight list, still
    # sets the content indent, so its indented continuation paragraph is prose
    assert semicolon_lines("Steps to follow:\n- Open the file.\n\n    Then save it; close it.\n") == [4]
    assert semicolon_lines("- Open the file.\n  - Pick a row.\n\n      Then save it; close it.\n") == [4]
    assert semicolon_lines("- Item\ncontinued\n\n    More; text.") == [4]
    assert semicolon_lines("Intro text.\n\n    x = 1; y = 2\n") == []
    assert semicolon_lines("Steps:\n- Open the file.\n\n      x = 1; y = 2\n") == []
    # a code span may wrap across lines of one paragraph
    assert semicolon_lines("Run `a;\nb; c` now; then") == [2]
    assert semicolon_lines("Run ``a`;\nb;`` now.") == []
    # a run that nothing closes in the paragraph is literal text
    assert semicolon_lines("A ` mark; here.\n\nAnd ` there; too.") == [1, 3]
    # a code span never crosses a block boundary: a new list item, a heading,
    # a fence, a quote-only line, or a change of quote depth
    assert semicolon_lines("- Press the ` key; it opens.\n- Run `x` now.\n") == [1]
    assert semicolon_lines("Press the ` key; it opens.\n# Run `x` now\n") == [1]
    assert semicolon_lines("Type ` to start; then stop.\n```\ncode\n```\nThe ` mark ends it.\n") == [1]
    assert semicolon_lines("> A ` mark; here.\n>\n> And ` there; too.\n") == [1, 3]
    assert semicolon_lines("# Title ` x\nText; with ` more\n") == [2]
    assert semicolon_lines("A ` mark; here.\n---\nAnd ` there; too.") == [1, 3]
    assert semicolon_lines("> A ` mark; here.\n> > And ` there; too.") == [1, 2]
    # a span still wraps inside a list item and a quote, also with a double run
    assert semicolon_lines("Run `a;\nb` now.\n") == []
    assert semicolon_lines("- Run `a;\n  b` now.\n") == []
    assert semicolon_lines("> Run `a;\n> b` now.\n") == []
    assert semicolon_lines("Run ``a`;\nb;`` now.\n- Next `x;` y.") == []
    # the lookahead starts at the given index of the shared line list, with no slice
    assert _mask_code_spans("a ` b;", 0, ["x ` y", "", "e ` f"], 1) == ("a ` b;", 0)
    assert _mask_code_spans("a ` b;", 0, ["x ` y", "", "e ` f"], 0) == ("a     ", 1)
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
    # leading front matter is skipped except its description; line numbers after it stay true
    findings, words_total = lint(f"---\nname: x\ndescription: {twenty} {twenty}.\n"
                                 "tags:\n  - a and\n---\nThe job is robust.")
    assert [(f["line"], f["rule"]) for f in findings] == [
        (3, "long-sentence"), (7, "marketing-adjective")], findings
    assert words_total == 44, words_total
    # the description is one paragraph, in a quoted, plain or block scalar
    for text, expected in (
            ("---\nname: x\ndescription: Applies to `thor/` only; the rules are in a file.\n---\n\nText.\n",
             [(3, 37, "semicolon")]),
            ('---\ndescription: "Use it; then stop."\n---\n', [(2, 21, "semicolon")]),
            ("---\ndescription: >-\n    Use it\n    robustly; then stop.\nname: x\n---\n",
             [(4, 5, "marketing-adjective"), (4, 13, "semicolon")]),
            ("---\ndescription: Use `a\n  b; c` now; stop.\n---\n", [(3, 12, "semicolon")]),
            ("---\ndescription: ```\n---\n\nProse; here.\n", [(5, 6, "semicolon")]),
            ("---\n# note\nname: x\n---\n", []),
            ("---\nname: x\n# note; here\nsummary: a; b\n---\n", []),
            # a comment before the first key, and a comment after the value
            ("---\n# metadata\nname: robust-tool\ndescription: Read the file.\n---\n", []),
            ("---\ndescription: Read the file. # robust; note\n---\n", []),
            ("---\ndescription: \"Read the file.\" # robust; note\n---\n", []),
            ("---\ndescription: Use it\n  # robust; note\n---\n", []),
            ("---\ndescription: \"Use it\n  across; lines\" # robust\n---\n", [(3, 9, "semicolon")]),
            # a "#" in quotes, in a block scalar, or inside a word is text
            ("---\ndescription: \"Read # the; file.\"\n---\n", [(2, 25, "semicolon")]),
            ("---\ndescription: 'It''s robust' # c\n---\n", [(2, 21, "marketing-adjective")]),
            ("---\ndescription: >\n  a # robust; b\n---\n", [(3, 7, "marketing-adjective"), (3, 13, "semicolon")]),
            ("---\ndescription: a#b; c\n---\n", [(2, 17, "semicolon")]),
            # a comment after a block scalar has less indent than its text
            ("---\ndescription: |\n    Use it.\n  # robust; note\n---\n", []),
            # quoted keys, keys with spaces and keys with other characters are YAML
            ("---\n\"robust-kit\": patch\n---\n", []),
            ("---\nallowed-tools: Bash; Read\n---\n", []),
            ("---\n$schema: robust; y\n---\n", []),
            ("---\nrésumé: a; b\n---\n", [])):
        findings, _ = lint(text)
        assert [(f["line"], f["col"], f["rule"]) for f in findings] == expected, (text, findings)
    # a block that is not YAML is Markdown: thematic breaks around prose
    findings, _ = lint("---\n# Instructions\n\nStart; stop.\n\n- First.\n\n---\n")
    assert [(f["line"], f["rule"]) for f in findings] == [(4, "semicolon")], findings
    findings, _ = lint("---\nStart; stop.\n---\n")
    assert [(f["line"], f["rule"]) for f in findings] == [(2, "semicolon")], findings
    # a plain key with a space reads as prose, as in "Step 1: run it"
    findings, _ = lint("---\nStep 1: run it; then: stop.\n---\n")
    assert [(f["line"], f["rule"]) for f in findings] == [(2, "semicolon")], findings
    # a block of comments only is Markdown: a heading between thematic breaks
    findings, _ = lint("---\n# Note\n---\n\nText; here.\n")
    assert [(f["line"], f["rule"]) for f in findings] == [(5, "semicolon")], findings
    # a later --- pair is a thematic break, not front matter
    findings, _ = lint(f"Intro.\n\n---\n{twenty} {twenty}.\n---")
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
                    "<details>\n\n~~~\n</details>\n~~~"):
        findings, _ = lint(f"{content}\n\n> [!NOTE]\n> {body}\n\n</details>")
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (content, findings)
    # Directly after <details>, ~~~ is HTML text, not a fence. So the </details> line after
    # it closes the container, and the alert after it is outside, as GitHub shows it.
    findings, _ = lint(f"<details>\n~~~\n</details>\n~~~\n\n> [!NOTE]\n> {body}\n\n</details>")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
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
        # repeated --disable flags add up instead of replacing each other
        with open(paths[0], "w", encoding="utf-8") as fh:
            fh.write("a; b. " + " ".join(["word"] * 30) + ".\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert main([paths[0], "--json", "--disable", "semicolon",
                         "--disable", "long-sentence"]) == 0
        assert json.loads(out.getvalue())["count"] == 0, out.getvalue()
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
    # an HTML block in a block quote holds text, and it ends with its quote
    findings, _ = lint("> <div>\n> ```\n> This is prose; keep it.\n> ```\n> </div>")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 3)], findings
    findings, _ = lint("> <div>\n\n```\nx; y\n```\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 7)], findings
    # a ">" line in an open HTML block is its text, not a quote end
    findings, _ = lint("<div>\n> Note.\n>\n> ```\n> a; b\n> ```\n</div>")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 5)], findings
    findings, _ = lint("<div>\n>\n```\nText; here.\n```")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 4)], findings
    # a quote after a paragraph starts a block quote, so a type 7 tag in it starts a block
    findings, _ = lint("Paragraph.\n> <widget>\n> ```\n> Text; here.\n> ```")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 4)], findings
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
    parser.add_argument("--disable", type=_rule_list, action="append", default=[],
                        metavar="RULES",
                        help="comma-separated rule IDs to silence; may be repeated")
    parser.add_argument("--selftest", action="store_true", help="run the built-in tests")
    # intermixed parsing keeps flags valid between file paths
    args = parser.parse_intermixed_args(argv)
    if args.selftest:
        selftest()
        return 0
    as_json, baseline, paths = args.json, args.baseline, args.paths
    disabled = set().union(*args.disable)

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
