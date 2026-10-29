"""Character rules of ste-lint: invisible characters and words of mixed scripts."""
import unittest

from ste_lint_fixture import has, rules
from ste_rules import HARD_IDS

INVISIBLE = "invisible-character"
MIXED = "mixed-script-word"
CYRILLIC_O = "о"


class InvisibleTests(unittest.TestCase):
    def test_no_break_space(self):
        found = rules("Use a space.", INVISIBLE)
        self.assertEqual([(f["line"], f["col"], f["match"]) for f in found], [(1, 6, "U+00A0")])

    def test_zero_width_space(self):
        self.assertEqual(rules("Use a​space.", INVISIBLE)[0]["match"], "U+200B")

    def test_bom(self):
        self.assertEqual(rules("﻿Use it.", INVISIBLE)[0]["match"], "U+FEFF")

    def test_each_occurrence(self):
        self.assertEqual(len(rules("a b\nc​d", INVISIBLE)), 2)

    def test_ordinary_whitespace_clean(self):
        self.assertFalse(has("Use\ta tab.\nThen a line.\r\n", INVISIBLE))

    def test_plain_prose_clean(self):
        self.assertEqual(rules("Open the file. Read it."), [])


class MixedScriptTests(unittest.TestCase):
    def test_cyrillic_in_code_span(self):
        found = rules("Edit `c%snfig.yaml` now." % CYRILLIC_O, MIXED)
        self.assertEqual(len(found), 1)
        self.assertIn("U+043E", found[0]["message"])

    def test_cyrillic_in_prose(self):
        self.assertTrue(has("Open the c%snfig file." % CYRILLIC_O, MIXED))

    def test_accented_word_clean(self):
        self.assertFalse(has("Open the café menu.", MIXED))

    def test_single_script_words_clean(self):
        self.assertFalse(has("日本語 привет config", MIXED))

    def test_japanese_word_of_two_scripts_clean(self):
        self.assertFalse(has("設定を食べる", MIXED))

    def test_ascii_with_greek_letter(self):
        self.assertTrue(has("Set the αlpha flag.", MIXED))


class RegistrationTests(unittest.TestCase):
    def test_rules_are_hard(self):
        self.assertIn(INVISIBLE, HARD_IDS)
        self.assertIn(MIXED, HARD_IDS)


if __name__ == "__main__":
    unittest.main()
