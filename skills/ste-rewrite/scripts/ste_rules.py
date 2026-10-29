"""The rules of ste-lint: one pattern for each rule, and the findings of one text.

Each pattern is a heuristic, not a parser. A rule may carry a `skip` function
that drops a match which the pattern cannot judge alone, such as a noun that
ends in -ed. Hedges and modality are never flagged, because confidence is
content. The word lists live in ste_words.
"""
import re
from collections import namedtuple

from ste_blocks import scan
from ste_chars import invisible_characters, mixed_script_words
from ste_text import long_sentences, word_before
from ste_words import (AUXILIARIES, CONSONANT_Y, DETERMINERS, DOUBLING_CONSONANTS,
                       EMPTY_VERBS, EXTRA_FORMS, GAP_WORDS, GERUND_ING, GERUND_PREPOSITIONS,
                       IDIOM, IRREGULAR, MARKETING_ADJECTIVES, MAX_GAP_WORDS, MODALS,
                       NOMINAL_ADJECTIVES, NOMINALS, NOT_PARTICIPLE, NOUN_BEFORE, PAST_D,
                       PAST_ED, PAST_IED, PERFECT_AUXILIARIES, PHRASAL_VERBS, PLURAL_ES,
                       PLURAL_IES, PLURAL_S, SIBILANT_ENDINGS, SILENT_E, SYNONYMS, TRANSITIVE,
                       VOWELS)

HARD = "hard"
ADVISORY = "advisory"
TO_IDIOM = " to "            # "is used to run" is an idiom, not a passive
MIN_PARTICIPLE_STEM = 2      # "red" and "bed" are too short to be participles
SENTENCE_BREAK = re.compile(r"[.!?:;]")
SEMICOLON_MARK = re.compile(r";")
SEMICOLON = "semicolon"
PHRASAL_VERB = "phrasal-verb"
MARKETING_ADJECTIVE = "marketing-adjective"
NOMINALIZATION = "nominalization"
PASSIVE_VOICE = "passive-voice"
PRESENT_PERFECT = "present-perfect"
LONG_SENTENCE = "long-sentence"
SYNONYM_ROTATION = "synonym-rotation"
DANGLING_CONJUNCTION = "dangling-conjunction"
INVISIBLE_CHARACTER = "invisible-character"
MIXED_SCRIPT = "mixed-script-word"

SEMICOLON_MESSAGE = "Split it into two sentences."
PHRASAL_VERB_MESSAGE = "Use one plain verb (start, contact, read, begin, expire)."
MARKETING_ADJECTIVE_MESSAGE = "Delete it, or give the measurement."
NOMINALIZATION_MESSAGE = "Use the verb (analyze, not perform an analysis)."
PASSIVE_VOICE_MESSAGE = "Name the actor. Use an active verb."
PRESENT_PERFECT_MESSAGE = "Use the simple past or present."


def _any_of(words):
    return r"(?:" + "|".join(words) + r")"


GAP = r"(?:" + _any_of(GAP_WORDS) + r"\s+){0," + str(MAX_GAP_WORDS) + r"}"
PARTICIPLE = r"\w{%d,}(?:ed|en)" % MIN_PARTICIPLE_STEM
PASSIVE_PARTICIPLE = r"\w{%d,}ed" % MIN_PARTICIPLE_STEM
AUXILIARY = _any_of(AUXILIARIES)
PERFECT = _any_of(PERFECT_AUXILIARIES)
DETERMINER = _any_of(DETERMINERS)
MODAL_BEFORE = re.compile(r"\b" + _any_of(MODALS) + r"(?:\s+not|n?['’]t)?\s+$", re.I)
GERUND_AFTER = r"(?!\s+(?:" + "|".join(GERUND_PREPOSITIONS) + r")\s+\w+ing)"
# A short vowel before one consonant doubles that consonant: "stop" gives "stopped".
CONSONANT_VOWEL_CONSONANT = re.compile(
    r"\w*[^%s][%s][%s]" % (VOWELS, VOWELS, DOUBLING_CONSONANTS))

Rule = namedtuple("Rule", "name level pattern message skip")


def _skip_passive(piece, found):
    """Drop a false passive: a non-participle, or an idiom such as "is used to"."""
    word = found.group("part").lower()
    return (word in NOT_PARTICIPLE
            or (word in IDIOM and piece[found.end():].startswith(TO_IDIOM)))


def _skip_perfect(piece, found):
    """Drop a non-participle, and a compound tense that a modal governs."""
    return (found.group("part").lower() in NOT_PARTICIPLE
            or bool(MODAL_BEFORE.search(piece[:found.start()])))


RULES = (
    Rule(SEMICOLON, HARD, SEMICOLON_MARK, SEMICOLON_MESSAGE, None),
    Rule(PHRASAL_VERB, HARD,
         re.compile(r"\b" + _any_of(PHRASAL_VERBS) + r"\b", re.I),
         PHRASAL_VERB_MESSAGE, None),
    Rule(MARKETING_ADJECTIVE, HARD,
         re.compile(r"\b" + _any_of(MARKETING_ADJECTIVES) + r"\b", re.I),
         MARKETING_ADJECTIVE_MESSAGE, None),
    Rule(NOMINALIZATION, HARD,
         re.compile(r"\b" + _any_of(EMPTY_VERBS) + r"\s+" + DETERMINER + r"\s+(?:"
                    + _any_of(NOMINAL_ADJECTIVES) + r"\s+)?" + _any_of(NOMINALS) + r"\b", re.I),
         NOMINALIZATION_MESSAGE, None),
    Rule(PASSIVE_VOICE, ADVISORY,
         re.compile(r"\b" + AUXILIARY + r"\s+" + GAP + r"(?P<part>" + PASSIVE_PARTICIPLE + r"|"
                    + _any_of(TRANSITIVE) + r")\b" + GERUND_AFTER, re.I),
         PASSIVE_VOICE_MESSAGE, _skip_passive),
    Rule(PRESENT_PERFECT, ADVISORY,
         re.compile(r"\b" + PERFECT + r"\s+" + GAP + r"(?:been\s+)?" + GAP + r"(?P<part>"
                    + PARTICIPLE + r"|" + _any_of(IRREGULAR) + r")\b", re.I),
         PRESENT_PERFECT_MESSAGE, _skip_perfect),
)
LEVEL_OF = dict([(rule.name, rule.level) for rule in RULES]
                + [(LONG_SENTENCE, HARD), (SYNONYM_ROTATION, HARD),
                   (DANGLING_CONJUNCTION, HARD), (INVISIBLE_CHARACTER, HARD),
                   (MIXED_SCRIPT, HARD)])
RULE_IDS = list(LEVEL_OF)
HARD_IDS = [name for name, level in LEVEL_OF.items() if level == HARD]
ADVISORY_IDS = [name for name, level in LEVEL_OF.items() if level == ADVISORY]


def _forms(word):
    """Return the inflections of one verb, so that "deleting" matches "delete"."""
    out = {word, word + PLURAL_S, word + PAST_ED, word + GERUND_ING}
    if word.endswith(SILENT_E):
        out |= {word + PAST_D, word[:-1] + GERUND_ING}
    if word.endswith(CONSONANT_Y):
        out |= {word[:-1] + PLURAL_IES, word[:-1] + PAST_IED}
    if word.endswith(SIBILANT_ENDINGS):
        out |= {word + PLURAL_ES}
    if CONSONANT_VOWEL_CONSONANT.fullmatch(word):
        out |= {word + word[-1] + PAST_ED, word + word[-1] + GERUND_ING}
    return out | set(EXTRA_FORMS.get(word, ()))


BASE_OF = {form: word for group in SYNONYMS for word in group for form in _forms(word)}
SYNONYM_RE = re.compile(r"\b(" + "|".join(sorted(BASE_OF, key=len, reverse=True)) + r")\b", re.I)


def _is_noun_use(piece, found):
    """True when the word before the match makes this word a noun.

    A sentence end counts as no word before, so "the log. Remove it" keeps the
    verb reading of "remove".
    """
    before = word_before(piece[:found.start()])
    if not before or SENTENCE_BREAK.search(before[1]):
        return False
    return before[0].lower() in NOUN_BEFORE


def lint(text, name, cap):
    """Return the findings of one text, sorted by line and column."""
    blocks, dangling = scan(text)
    found = []

    def add(line, col, rule, match, message):
        found.append({"file": name, "line": line, "col": col, "rule": rule,
                      "level": LEVEL_OF[rule], "match": match, "message": message})

    seen = {}
    for block in blocks:
        for lineno, col, piece in block:
            for rule in RULES:
                for hit in rule.pattern.finditer(piece):
                    if rule.skip and rule.skip(piece, hit):
                        continue
                    add(lineno, col + hit.start() + 1, rule.name, hit.group(0), rule.message)
            for hit in SYNONYM_RE.finditer(piece):
                if _is_noun_use(piece, hit):
                    continue
                base = BASE_OF[hit.group(1).lower()]
                seen.setdefault(base, (lineno, col + hit.start() + 1, hit.group(1)))
        for lineno, col, count in long_sentences(block, cap):
            add(lineno, col, LONG_SENTENCE, f"{count} words",
                f"Sentence has {count} words (cap {cap}). Split it.")
    for group in SYNONYMS:
        used = sorted((seen[word], word) for word in group if word in seen)
        for (lineno, col, match), word in used[1:]:
            add(lineno, col, SYNONYM_ROTATION, match,
                f"'{word}' repeats '{used[0][1]}'. Use '{used[0][1]}' only.")
    for lineno, col, word in dangling:
        add(lineno, col, DANGLING_CONJUNCTION, word,
            f"List item ends with '{word}'. Finish the item or join it to the next.")
    for rule, check in ((INVISIBLE_CHARACTER, invisible_characters),
                        (MIXED_SCRIPT, mixed_script_words)):
        for lineno, col, match, message in check(text):
            add(lineno, col, rule, match, message)
    found.sort(key=lambda finding: (finding["line"], finding["col"]))
    return found
