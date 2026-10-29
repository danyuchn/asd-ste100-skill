"""Markdown handling of ste-lint: skipped regions, positions, sentences, and list items."""
import time
import unittest

from ste_lint_fixture import BODY26, TWENTY, has, lint, rules


class MarkdownTests(unittest.TestCase):
    def test_footnote_definition_is_prose(self):
        self.assertTrue(has("[^1]: Note; here.", "semicolon"))

    def test_fence_indent_limit(self):
        self.assertTrue(has("    ```\na; b", "semicolon"))
        self.assertTrue(has(">     ```\n> a; b", "semicolon"))
        self.assertEqual(rules("   ```\na; b\n   ```", "semicolon"), [])

    def test_fence_inside_a_list_item(self):
        for text in ("- item\n    ```\n    a; b\n    ```",
                     "1. item\n   ```\n   a; b\n   ```",
                     "- item\n  - nested\n      ```\n      a; b\n      ```"):
            self.assertEqual(rules(text, "semicolon"), [], text)

    def test_skipped_regions(self):
        for text in ("```\nx = a; y = b\n```", "~~~\na; b\n~~~", "    a; b",
                     "---\ntitle: a; b\n---\nText.", "<div>a; b</div>",
                     "<!-- a; b -->", "<!--\na; b\n-->\nText.", "text <!-- a; b --> end"):
            self.assertEqual(lint(text), [], text)

    def test_unclosed_front_matter_is_not_skipped(self):
        self.assertTrue(has("---\na; b", "semicolon"))

    def test_indented_code_not_in_list(self):
        self.assertTrue(has("- item\n    a; b", "semicolon"))
        self.assertTrue(has("Wrapped line\n    a; b", "semicolon"))

    def test_masks_keep_columns(self):
        self.assertEqual(rules("`a; b` and c; d", "semicolon")[0]["col"], 13)
        for text in ("See [x](http://a.example/a;b) now.", "Use <https://a.example/a;b> now.",
                     "A&nbsp;B and a&#59; b.", "Run `a; b`."):
            self.assertEqual(rules(text, "semicolon"), [], text)

    def test_nested_paren_link_and_reference_definition(self):
        for text in ("See [x](https://en.wikipedia.org/wiki/Foo_(bar);x) now.",
                     '[id]: https://example.com/a;b "Title"'):
            self.assertEqual(rules(text, "semicolon"), [], text)

    def test_fence_close_rules(self):
        for text in ("````\na; b\n```\nc; d\n````", "~~~\na; b\n```\nc; d\n~~~",
                     "> ```\n> a; b\n> ```", "```\na; b\n~~~\nc; d\n```"):
            self.assertEqual(rules(text, "semicolon"), [], text)
        self.assertTrue(has("```\nx\n```\na; b", "semicolon"))

    def test_line_splitting(self):
        for sep, line in (("\r", 2), ("\r\n", 2), ("\n", 2), ("\x0b", 1), ("\x0c", 1), (" ", 1)):
            self.assertEqual(rules(f"a{sep}b; c", "semicolon")[0]["line"], line, repr(sep))

    def test_tables(self):
        cell = " ".join(f"term{n}" for n in range(1, 26)) + "."
        for table in (f"| A | B |\n| --- | --- |\n| x | {cell} |",
                      f"A | B\n:---: | ---:\nx | {cell}"):
            self.assertEqual(rules(table, "long-sentence"), [], table)
        long_cell = " ".join(f"term{n}" for n in range(1, 27)) + "."
        found = rules(f"| A | B |\n| --- | --- |\n| x; y | {long_cell} |")
        self.assertEqual([(f["rule"], f["line"], f["col"]) for f in found],
                         [("semicolon", 3, 4), ("long-sentence", 3, 10)])
        self.assertEqual(len(rules("| a; b |\n| --- |\n| c |", "semicolon")), 1)  # one column

    def test_table_separator_not_linted(self):
        self.assertEqual(rules("| A | B |\n| --- | --- |\n| x | y |"), [])

    def test_markers_are_not_words(self):
        n25 = " ".join(f"term{n}" for n in range(1, 26)) + "."
        for marker in ("-", "*", "+", "1.", "1)", "  -", "> -", "#", "> >"):
            self.assertEqual(rules(f"{marker} {n25}", "long-sentence"), [], marker)
        f = rules(f"- term0 {n25}", "long-sentence")
        self.assertEqual([(x["match"], x["col"]) for x in f], [("26 words", 3)])
        self.assertEqual(rules("> " + "\n> ".join(["word word word word word"] * 5) + ".",
                               "long-sentence"), [])

    def test_alert_markers(self):
        for alert in ("> [!NOTE]", "> [!tip]", ">[!Warning]", ">  [!CAUTION]  ", "> [!important]"):
            self.assertEqual(rules(f"{alert}\n> {BODY26}", "long-sentence"), [], alert)
        self.assertEqual(len(rules(f"> [!FOO]\n> {BODY26}", "long-sentence")), 1)
        self.assertEqual(len(rules(f"> [!NOTE] {BODY26}", "long-sentence")), 1)

    def test_alert_marker_only_at_the_top_quote_level(self):
        self.assertEqual(len(rules(f"> > [!NOTE]\n> > {BODY26}", "long-sentence")), 1)

    def test_wrapped_sentence_counted_once(self):
        found = rules(f"Intro text here.\nThe {TWENTY}\nwrapped tail words go here.", "long-sentence")
        self.assertEqual([(f["line"], f["col"]) for f in found], [(2, 1)])
        self.assertTrue(has(f"- Item {TWENTY}\n  continued in the same item.", "long-sentence"))

    def test_block_boundaries_split(self):
        for sep in ("\n\n", "\n# Heading\n", "\n---\n", "\n- ", "\n1) ", "\n> ", "\n```\nx\n```\n",
                    "\n<hr>\n", "\n<!-- c -->\n", "\n| a | b |\n| --- | --- |\n"):
            self.assertEqual(rules(f"First {TWENTY} line{sep}Second {TWENTY} line.",
                                   "long-sentence"), [], repr(sep))
        for text in (f"- First item\n    - First {TWENTY} line\n      - Second {TWENTY} line",
                     f"> - First {TWENTY} line\n> - Second {TWENTY} line",
                     f"> First {TWENTY} line.\n>\n> Second {TWENTY} line."):
            self.assertEqual(rules(text, "long-sentence"), [], text)

    def test_abbreviations(self):
        self.assertTrue(has(f"Use a tool, e.g. the {TWENTY} linter here now.", "long-sentence"))
        self.assertTrue(has(f"Compare A vs. B in the {TWENTY} test.", "long-sentence"))
        self.assertTrue(has(f"See **e.g.** the {TWENTY} linter here now.", "long-sentence"))
        self.assertFalse(has(f"The team shipped it in the U.S. Then {TWENTY} today.", "long-sentence"))
        self.assertFalse(has(f'He asked "{TWENTY}?" Then {TWENTY} ended. (It {TWENTY}.) Next.',
                             "long-sentence"))

    def test_no_ends_a_sentence_without_a_number(self):
        self.assertEqual(rules(f"They said no. {BODY26}", "long-sentence"), [])
        self.assertTrue(has(f"Use No. 5 with {TWENTY} more words here now.", "long-sentence"))

    def test_ellipsis_ends_a_sentence_only_before_a_capital(self):
        self.assertTrue(has(f"The job waits... {TWENTY} more words here.", "long-sentence"))
        found = rules(f"Stop... The {TWENTY} more words go in here now.", "long-sentence")
        self.assertEqual([f["col"] for f in found], [9])

    def test_bold_lead(self):
        self.assertFalse(has(f"**Lead.** The {TWENTY} more words here now.", "long-sentence"))
        self.assertFalse(has(f"_Note._ The {TWENTY} more words here now.", "long-sentence"))

    def test_punctuation_is_not_a_word(self):
        for sep in (", ", " ", " / "):
            names = sep.join(f"`a{n}`" for n in range(30))
            self.assertEqual(rules(f"The adapters are {names}.", "long-sentence"), [])
        self.assertEqual(rules(" ".join(f"t{n}" for n in range(1, 25)) + " — t25.",
                               "long-sentence"), [])

    def test_max_words(self):
        text = " ".join(["word"] * 21) + "."
        self.assertFalse(has(text, "long-sentence"))
        self.assertTrue(has(text, "long-sentence", cap=20))

    def test_performance(self):
        start = time.time()
        found = lint("The agent read the log.\n" * 20000)
        self.assertLess(time.time() - start, 2)
        self.assertEqual(rules("The agent read the log.\n" * 3, "long-sentence"), [])
        self.assertFalse(any(f["rule"] == "long-sentence" for f in found))


class DanglingTests(unittest.TestCase):
    def dangling(self, text):
        return [(f["line"], f["col"]) for f in rules(text, "dangling-conjunction")]

    def test_all_markers(self):
        text = ("- Confirm the target and\n* Record the result OR  \n+ Close the panel\n"
                "1. Start the task and\n2) Stop the task OR")
        self.assertEqual(self.dangling(text), [(1, 1), (2, 1), (4, 1), (5, 1)])
        self.assertTrue(all(f["level"] == "hard" for f in rules(text, "dangling-conjunction")))

    def test_continuation(self):
        self.assertEqual(self.dangling("  - Confirm the target and\n    record the result."), [])
        self.assertEqual(self.dangling("- Confirm the target\n  and"), [(2, 3)])
        self.assertEqual(self.dangling("- Start the task and\n\n  record the result."), [])
        self.assertEqual(self.dangling("100. Start the task and\n  unrelated text"), [(1, 1)])
        self.assertEqual(self.dangling(" - Start the task and\n   record the result."), [])
        self.assertEqual(self.dangling("-  Start the task and\n   record the result."), [])

    def test_columns(self):
        self.assertEqual(self.dangling("   - Start the task and"), [(1, 4)])

    def test_nested(self):
        self.assertEqual(self.dangling("- Parent item and\n  - Nested item or"), [(1, 1), (2, 3)])

    def test_not_flagged(self):
        for text in ("    - code and", "The process may include steps and",
                     "- Start the task and.\n- Stop the task or,", "- Use `and` as a label",
                     "- Combine `left` and `right`", "```text\n- code and\n```",
                     "~~~\n- code and\n~~~", "> - Confirm the target and\n> - Record the result or"):
            self.assertEqual(self.dangling(text), [], text)

    def test_fenced_item_content(self):
        self.assertEqual(self.dangling("- Do this and\n~~~\ncode and\n~~~"), [(1, 1)])

    def test_inline_code_and(self):
        self.assertEqual(self.dangling("- Run `x` and `and`"), [])
        self.assertEqual(self.dangling("- Run `x` and"), [(1, 1)])

    def test_tab_after_marker(self):
        self.assertEqual(self.dangling("-\tStart the task and"), [(1, 1)])


if __name__ == "__main__":
    unittest.main()
