"""Characters a reader cannot see: invisible characters and words of mixed scripts.

Both checks read the raw text, because a code span or a code block is the worst
place for a hidden character. The sets come from unicodedata, not from a list.
"""
import re
import unicodedata

INVISIBLE_CATEGORIES = frozenset(("Cf", "Cc", "Zs", "Zl", "Zp"))
VISIBLE_WHITESPACE = frozenset((" ", "\t", "\n", "\r"))
LETTER_PREFIX = "L"
LATIN_SCRIPT = "LATIN"
WORD = re.compile(r"\w+")
CODE_POINT = "U+%04X"
UNNAMED = "UNNAMED"
INVISIBLE_MESSAGE = ("Invisible character %s (%s). Replace it with a space, "
                     "or remove it.")
MIXED_SCRIPT_MESSAGE = "Word mixes scripts: '%s' holds %s %s (%s). Use one script."


def _is_invisible(char):
    return (unicodedata.category(char) in INVISIBLE_CATEGORIES
            and char not in VISIBLE_WHITESPACE)


def _script(char):
    """Return the script name of a letter: the first word of its Unicode name."""
    return unicodedata.name(char, UNNAMED).split()[0]


def _letter_name(char):
    """Return the last word of the Unicode name, such as the letter in 'CYRILLIC SMALL LETTER O'."""
    return unicodedata.name(char, UNNAMED).split()[-1]


def invisible_characters(text):
    """Return (line, col, match, message) for each invisible character."""
    found = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for index, char in enumerate(line):
            if _is_invisible(char):
                point = CODE_POINT % ord(char)
                name = unicodedata.name(char, UNNAMED)
                found.append((lineno, index + 1, point, INVISIBLE_MESSAGE % (point, name)))
    return found


def mixed_script_words(text):
    """Return (line, col, word, message) for each word that holds a lookalike letter.

    A word qualifies only when it holds an ASCII letter and a letter of another
    script. A word of one foreign script is foreign text, and a Japanese word
    mixes two scripts by its own rules, so neither one is a lookalike.
    """
    found = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for hit in WORD.finditer(line):
            word = hit.group(0)
            letters = [c for c in word if unicodedata.category(c).startswith(LETTER_PREFIX)]
            if not any(c.isascii() for c in letters):
                continue
            odd = next((c for c in letters if _script(c) != LATIN_SCRIPT), None)
            if odd is None:
                continue
            found.append((lineno, hit.start() + 1, word, MIXED_SCRIPT_MESSAGE % (
                word, _script(odd), _letter_name(odd), CODE_POINT % ord(odd))))
    return found
