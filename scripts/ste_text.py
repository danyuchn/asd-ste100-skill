"""Prose helpers: code masking, word counts, and sentence length."""
import bisect
import re

from ste_rules import MAX_WORDS


INLINE_CODE = re.compile(r"`[^`]*`")
# Markup that is not prose: character references (&nbsp; &#39; &#x2192;),
# inline link destinations ("](url"), and autolinks (<https://...>).
NON_PROSE = re.compile(
    r"&(?:[A-Za-z][A-Za-z0-9]{1,31}|#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6});"
    r"|(?<=\]\()[^)\s]+"
    r"|<[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\s]*>"
)
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


def _count_words(text):
    """Count whitespace-separated tokens that contain a letter or a digit.

    Bare punctuation is not a word: a comma left behind by a masked code
    span, or a spaced em dash, does not make a sentence longer.
    """
    return sum(1 for token in text.split() if WORD_CHAR.search(token))


def _mask_inline_code(text):
    """Blank code spans with equal-length spaces so columns stay true."""
    return INLINE_CODE.sub(lambda match: " " * len(match.group(0)), text)


def _mask_non_prose(text):
    """Blank code spans, then fill character references and link targets.

    The fill is underscores, not spaces, so a token stays one token and word
    counts do not change. An underscore is not a word character for _count_words.
    """
    return NON_PROSE.sub(lambda match: "_" * len(match.group(0)),
                         _mask_inline_code(text))


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
