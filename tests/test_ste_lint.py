"""Tests for skills/rewrite/scripts/ste-lint: decisions, positions, and exit codes."""
import importlib.machinery
import json
import os
import subprocess
import sys
import tempfile
import time
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "rewrite", "scripts", "ste-lint")
sys.dont_write_bytecode = True  # keep __pycache__ out of the plugin scripts/ folder
_loader = importlib.machinery.SourceFileLoader("ste_lint", SCRIPT)
ste = types.ModuleType(_loader.name)
_loader.exec_module(ste)

TWENTY = " ".join(["word"] * 20)
BODY26 = " ".join(["word"] * 25) + "."  # 25 words; a marker word would make 26


def lint(text, cap=25):
    return ste.lint(text, "t.md", cap)


def rules(text, rule=None, cap=25):
    found = lint(text, cap)
    return [f for f in found if rule is None or f["rule"] == rule]


def has(text, rule, cap=25):
    return bool(rules(text, rule, cap))


def run(args, stdin=None):
    return subprocess.run([sys.executable, SCRIPT] + args, input=stdin,
                          capture_output=True, text=True)


class RuleTests(unittest.TestCase):
    def test_each_rule_fires(self):
        text = ("The panel is removed; spin up the job. "
                "Perform an analysis of the seamless log. We have received the report.")
        got = {f["rule"] for f in lint(text)}
        for rule in ("semicolon", "phrasal-verb", "nominalization", "marketing-adjective",
                     "passive-voice", "present-perfect"):
            self.assertIn(rule, got)
        self.assertTrue(has(" ".join(["word"] * 30) + ".", "long-sentence"))

    def test_levels(self):
        for f in lint("The panel is removed; we have run it."):
            self.assertEqual(f["level"], "advisory" if f["rule"] in
                             ("passive-voice", "present-perfect") else "hard")

    def test_hedges_clean(self):
        self.assertEqual(lint("The request may have failed. It could be a timeout. "
                              "The disk might have filled."), [])

    def test_irregular_participles(self):
        self.assertEqual(len(rules("The task has run. We have begun. The job has set the flag.",
                                   "present-perfect")), 3)
        self.assertTrue(has("The job has run.", "present-perfect"))
        self.assertFalse(has("The job may have run.", "present-perfect"))

    def test_modal_protection(self):
        for modal in ("may", "might", "could", "should", "would", "must", "can", "will", "shall"):
            for gap in (" ", "  ", "\t", " not "):
                self.assertFalse(has(f"The task {modal}{gap}have run.", "present-perfect"))
        self.assertFalse(has("The task couldn't have run. The task MAY NOT HAVE RUN.",
                             "present-perfect"))
        self.assertFalse(has("It can’t have run.", "present-perfect"))

    def test_passive(self):
        self.assertTrue(has("The flag is set.", "passive-voice"))
        self.assertFalse(has("The task is gone.", "passive-voice"))

    def test_nominalization_plural_ending(self):
        self.assertTrue(has("We perform the analyses of logs.", "nominalization"))

    def test_phrasal_and_marketing_cols(self):
        self.assertEqual(rules("Run `make all` then spin up the node.", "phrasal-verb")[0]["col"], 21)
        self.assertTrue(has("A robust and game-changing tool.", "marketing-adjective"))

    def test_semicolon_positive_and_position(self):
        f = rules("a\nb; c", "semicolon")[0]
        self.assertEqual((f["line"], f["col"]), (2, 2))


class MarkdownTests(unittest.TestCase):
    def test_footnote_definition_is_prose(self):
        self.assertTrue(has("[^1]: Note; here.", "semicolon"))

    def test_fence_indent_limit(self):
        self.assertTrue(has("    ```\na; b", "semicolon"))
        self.assertTrue(has(">     ```\n> a; b", "semicolon"))
        self.assertEqual(rules("   ```\na; b\n   ```", "semicolon"), [])

    def test_nominalization_osis_esis(self):
        self.assertTrue(has("Perform a diagnosis of the unit.", "nominalization"))
        self.assertTrue(has("Carry out the diagnoses.", "nominalization"))
        self.assertTrue(has("Perform a synthesis of the data.", "nominalization"))

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
        for sep, line in (("\r", 2), ("\r\n", 2), ("\n", 2), ("\x0b", 1), ("\x0c", 1), ("\u2028", 1)):
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
        self.assertEqual(len(rules("| a; b |\n| --- |\n| c |", "semicolon")), 1)  # one column: plain prose

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
        self.assertIn("20", rules(text, "long-sentence", cap=20)[0]["message"])

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


class SynonymTests(unittest.TestCase):
    def test_positive(self):
        found = rules("Check the config file. Then verify the output. Verify twice.", "synonym-rotation")
        self.assertEqual([(f["line"], f["col"], f["match"]) for f in found], [(1, 29, "verify")])
        self.assertIn("verify", found[0]["message"])
        self.assertIn("check", found[0]["message"])

    def test_negative(self):
        self.assertFalse(has("Check the config. Check the output. Checked twice.", "synonym-rotation"))
        self.assertFalse(has("Delete the file. Show the log.", "synonym-rotation"))

    def test_correct_is_not_rotated(self):
        self.assertFalse(has("Correct the file. Fix the log.", "synonym-rotation"))

    def test_document_order_and_masking(self):
        found = rules("Remove it.\nDelete it.\nErase it.", "synonym-rotation")
        self.assertEqual([f["line"] for f in found], [2, 3])
        self.assertFalse(has("Remove `delete` it.", "synonym-rotation"))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, text):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_exit_0(self):
        r = run([], "Short line here.\n")
        self.assertEqual((r.returncode, r.stdout), (0, "0 findings (0 hard, 0 advisory, baseline 0)\n"))

    def test_exit_1_and_text_format(self):
        r = run([], "The panel is removed; spin up the job.\n")
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertRegex(lines[0], r"^<stdin>:1:\d+: \w[\w-]*: .+ \[.+\]$")
        self.assertEqual(lines[-1], "3 findings (2 hard, 1 advisory, baseline 0)")

    def test_advisory_never_fails(self):
        self.assertEqual(run([], "The flag is set. We have run it.\n").returncode, 0)

    def test_baseline(self):
        text = "a; b; c.\n"
        self.assertEqual(run(["--baseline", "1"], text).returncode, 1)
        r = run(["--baseline", "2"], text)
        self.assertEqual(r.returncode, 0)
        self.assertIn("baseline 2", r.stdout)

    def test_disable(self):
        self.assertEqual(run(["--disable", "semicolon"], "a; b.\n").returncode, 0)
        self.assertEqual(run(["--disable", "semicolon,passive-voice"], "a; b.\n").returncode, 0)

    def test_unknown_rule(self):
        r = run(["--disable", "nope"], "a\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("dangling-conjunction", r.stderr)

    def test_bad_numbers_and_flags(self):
        for args in (["--baseline", "x"], ["--baseline", "-1"], ["--max-words", "0"],
                     ["--max-words", "x"], ["--basel", "1"], ["--nope"], ["--baseline"]):
            self.assertEqual(run(args, "a\n").returncode, 2, args)

    def test_unreadable_file(self):
        r = run([os.path.join(self.tmp.name, "missing.md")])
        self.assertEqual(r.returncode, 2)
        self.assertIn("cannot read", r.stderr)
        bad = self.write("bad.md", "")
        with open(bad, "wb") as fh:
            fh.write(b"\xff\xfe\x00")
        self.assertEqual(run([bad]).returncode, 2)

    def test_stdin_and_dash(self):
        self.assertEqual(run(["-"], "a; b.\n").returncode, 1)
        self.assertTrue(run(["-"], "a; b.\n").stdout.startswith("<stdin>:1:2:"))

    def test_bom_is_ignored(self):
        data = "\ufeffa; b.\n".encode("utf-8")
        r = subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True)
        self.assertTrue(r.stdout.decode().startswith("<stdin>:1:2:"), r.stdout)
        path = os.path.join(self.tmp.name, "bom.md")
        with open(path, "wb") as fh:
            fh.write(data)
        self.assertTrue(run([path]).stdout.startswith(path + ":1:2:"))

    def test_stdin_decode_error_names_stdin(self):
        r = subprocess.run([sys.executable, SCRIPT], input=b"\xff\xfe\x00", capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("cannot read <stdin>", r.stderr.decode())

    def test_max_words_flag(self):
        text = " ".join(["word"] * 21) + ".\n"
        self.assertEqual(run([], text).returncode, 0)
        self.assertEqual(run(["--max-words", "20"], text).returncode, 1)

    def test_flags_between_files(self):
        a = self.write("a.md", "Short line here.\n")
        b = self.write("b.md", "Another short line.\n")
        r = run([a, "--json", b])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["findings"], [])

    def test_order_across_files(self):
        a = self.write("a.md", "x\ny; z\n")
        b = self.write("b.md", "p; q\n")
        out = run([b, a]).stdout.splitlines()
        self.assertTrue(out[0].startswith(b + ":1:2:"))
        self.assertTrue(out[1].startswith(a + ":2:2:"))

    def test_limit(self):
        text = "a; b.\n" * 5
        r = run(["--limit", "2"], text)
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[-1].startswith("5 findings (5 hard, 0 advisory, baseline 0)"))
        self.assertTrue(lines[-1].endswith(", 3 not shown (use --limit 0 or --json)"))
        self.assertEqual(len(run(["--limit", "0"], text).stdout.splitlines()), 6)
        self.assertEqual(len(run([], text).stdout.splitlines()), 6)
        self.assertNotIn("not shown", run(["--limit", "5"], text).stdout)
        self.assertEqual(len(json.loads(run(["--json", "--limit", "1"], text).stdout)["findings"]), 5)
        self.assertEqual(run(["--limit", "-1"], text).returncode, 2)
        self.assertEqual(run(["--limit", "x"], text).returncode, 2)
        self.assertEqual(run(["--limit", "1", "--baseline", "5"], text).returncode, 0)

    def test_help(self):
        r = run(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertLessEqual(len(r.stdout.splitlines()), 32)
        for word in ("--limit", "--max-words", "semicolon", "advisory", "exit codes", "docs/*.md"):
            self.assertIn(word, r.stdout)

    def test_errors_go_to_stderr(self):
        for args in (["--baseline", "x"], ["--disable", "nope"], ["/nonexistent/x.md"]):
            r = run(args, "a\n")
            self.assertEqual((r.returncode, r.stdout), (2, ""), args)
            self.assertIn("ste-lint: error:", r.stderr)
        self.assertIn("expected an integer", run(["--baseline", "x"]).stderr)

    def test_json_shape(self):
        r = run(["--json", "--baseline", "3"], "a; b. The flag is set.\n")
        data = json.loads(r.stdout)
        self.assertEqual(set(data), {"findings", "hard", "baseline"})
        self.assertEqual((data["hard"], data["baseline"]), (1, 3))
        self.assertEqual(r.returncode, 0)
        for f in data["findings"]:
            self.assertEqual(set(f), {"file", "line", "col", "rule", "level", "match", "message"})
            self.assertIn(f["level"], ("hard", "advisory"))


if __name__ == "__main__":
    unittest.main()
