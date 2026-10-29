"""Text level work for ste-lint: masking, sentence borders, and word counts.

Masking blanks a span with fill of the same length, so a line keeps its true
columns. A rule never reads code, a link target, or an entity.
"""
import bisect
import re

from ste_words import ABBREVIATIONS, NUMBERED

BLANK = " "       # fill that removes a span from the rules and from the word count
KEEP = "#"        # fill that removes a span from the rules and keeps one word
TAB_WIDTH = 4     # CommonMark counts a tab as 4 columns of indentation

# Spans blanked before any rule runs: code, link URLs, autolinks, entities.
CODE_SPAN = r"`[^`]*`"
LINK_TARGET = r"(?<=\])\((?:[^()]|\([^()]*\))*\)"
AUTOLINK = r"<[a-z][a-z0-9+.-]*:[^>\s]*>"
ENTITY = r"&(?:#x?[0-9a-f]+|[a-z][a-z0-9]*);"
MASK = re.compile("|".join((CODE_SPAN, LINK_TARGET, AUTOLINK, ENTITY)), re.I)

LINE_BREAK = re.compile(r"\r\n|\n|\r")  # the line endings of CommonMark
QUOTE = re.compile(r"^ {0,3}(?:> ?)+")
WORD = re.compile(r"\S+")
WORD_CHAR = re.compile(r"[^\W_]")
TRAILING_WORD = re.compile(r"([^\W_]+)([^\w]*)$")
CLOSERS = r"[\"'”’)\]*_]*"  # quotes and emphasis that may follow a stop mark
SENTENCE_END = re.compile(r"[.!?]" + CLOSERS + r"$")
ELLIPSIS = re.compile(r"(?:\.\.\.|…)" + CLOSERS + r"$")
OPENERS = "\"'“‘([*_"
DOTTED = re.compile(r"(?:[a-z]\.){2,}", re.I)


def mask(text, fill=BLANK):
    """Blank spans with equal-length fill, so columns stay true."""
    return MASK.sub(lambda m: fill * len(m.group()), text)


def prefix_length(raw):
    quote = QUOTE.match(raw)
    return quote.end() if quote else 0


def view(raw, fill=BLANK):
    """Return the masked line with its quote prefix blanked, and the prefix length."""
    pre = prefix_length(raw)
    return BLANK * pre + mask(raw, fill)[pre:], pre


def indent_of(text):
    expanded = text.expandtabs(TAB_WIDTH)
    return len(expanded) - len(expanded.lstrip(BLANK))


def word_before(text):
    """Return (word, separator) for the last word of text, or None."""
    found = TRAILING_WORD.search(text)
    return (found.group(1), found.group(2)) if found else None


def sentence_starts(text):
    """Return the offset of each sentence start. One linear pass over the words."""
    words = list(WORD.finditer(text))
    if not words:
        return [0]
    starts = [words[0].start()]
    for word, nxt in zip(words, words[1:]):
        token = word.group()
        end = SENTENCE_END.search(token)
        if not end:
            continue
        core = token[:end.start() + 1].lstrip(OPENERS)
        low = core.lower()
        if low in ABBREVIATIONS:
            continue
        head = nxt.group().lstrip(OPENERS)[:1]
        if low in NUMBERED and head.isdigit():
            continue
        if ELLIPSIS.search(token) and not head.isupper():
            continue
        if DOTTED.fullmatch(core) and not head.isupper():
            continue
        starts.append(nxt.start())
    return starts


def count_words(text):
    """Return the number of tokens that hold a letter or a digit."""
    return sum(1 for token in text.split() if WORD_CHAR.search(token))


def long_sentences(block, cap):
    """Yield (line, col, word count) for each sentence over the cap in one block."""
    offsets, pos = [], 0
    for _, _, piece in block:
        offsets.append(pos)
        pos += len(piece) + len(BLANK)
    joined = BLANK.join(piece for _, _, piece in block)
    starts = sentence_starts(joined)
    for start, end in zip(starts, starts[1:] + [len(joined)]):
        count = count_words(joined[start:end])
        if count > cap:
            index = bisect.bisect_right(offsets, start) - 1
            lineno, col, _ = block[index]
            yield lineno, col + start - offsets[index] + 1, count
