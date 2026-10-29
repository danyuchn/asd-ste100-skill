"""Command line behavior of ste-lint: exit codes, output format, and flags."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from ste_lint_fixture import SCRIPT, run


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
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[-1:], [r.stdout.rstrip("\n")])
        data = json.loads(run(["--json"], "Short line here.\n").stdout)
        self.assertEqual((len(data["findings"]), data["hard"]), (0, 0))

    def test_exit_1_and_text_format(self):
        r = run([], "The panel is removed; spin up the job.\n")
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertRegex(lines[0], r"^<stdin>:1:\d+: \w[\w-]*: .+ \[.+\]$")
        data = json.loads(run(["--json"], "The panel is removed; spin up the job.\n").stdout)
        self.assertEqual((len(data["findings"]), data["hard"]), (3, 2))

    def test_advisory_never_fails(self):
        self.assertEqual(run([], "The flag is set. We have run it.\n").returncode, 0)

    def test_baseline(self):
        text = "a; b; c.\n"
        self.assertEqual(run(["--baseline", "1"], text).returncode, 1)
        r = run(["--baseline", "2"], text)
        self.assertEqual(r.returncode, 0)

    def test_disable(self):
        self.assertEqual(run(["--disable", "semicolon"], "a; b.\n").returncode, 0)
        self.assertEqual(run(["--disable", "semicolon,passive-voice"], "a; b.\n").returncode, 0)

    def test_disable_invisible_character(self):
        text = "Use a\u00a0space.\n"
        self.assertEqual(run([], text).returncode, 1)
        self.assertEqual(run(["--disable", "invisible-character"], text).returncode, 0)

    def test_unknown_rule(self):
        self.assertEqual(run(["--disable", "nope"], "a\n").returncode, 2)

    def test_bad_numbers_and_flags(self):
        for args in (["--baseline", "x"], ["--baseline", "-1"], ["--max-words", "0"],
                     ["--max-words", "x"], ["--basel", "1"], ["--nope"], ["--baseline"]):
            self.assertEqual(run(args, "a\n").returncode, 2, args)

    def test_unreadable_file(self):
        self.assertEqual(run([os.path.join(self.tmp.name, "missing.md")]).returncode, 2)
        bad = self.write("bad.md", "")
        with open(bad, "wb") as fh:
            fh.write(b"\xff\xfe\x00")
        self.assertEqual(run([bad]).returncode, 2)

    def test_stdin_and_dash(self):
        r = run(["-"], "a; b.\n")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("<stdin>:1:2:"))

    def test_bom_is_ignored(self):
        data = "﻿a; b.\n".encode("utf-8")
        r = subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True)
        self.assertTrue(r.stdout.decode().startswith("<stdin>:1:2:"), r.stdout)
        path = os.path.join(self.tmp.name, "bom.md")
        with open(path, "wb") as fh:
            fh.write(data)
        self.assertTrue(run([path]).stdout.startswith(path + ":1:2:"))

    def test_stdin_decode_error_exits_2(self):
        r = subprocess.run([sys.executable, SCRIPT], input=b"\xff\xfe\x00", capture_output=True)
        self.assertEqual(r.returncode, 2)

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
        self.assertEqual(len(json.loads(run(["--json", "--limit", "1"], text).stdout)["findings"]), 5)
        self.assertEqual(run(["--limit", "-1"], text).returncode, 2)
        self.assertEqual(run(["--limit", "x"], text).returncode, 2)
        self.assertEqual(run(["--limit", "1", "--baseline", "5"], text).returncode, 0)

    def test_help_exits_0(self):
        self.assertEqual(run(["--help"]).returncode, 0)

    def test_errors_go_to_stderr(self):
        for args in (["--baseline", "x"], ["--disable", "nope"], ["/nonexistent/x.md"]):
            r = run(args, "a\n")
            self.assertEqual((r.returncode, r.stdout), (2, ""), args)
            self.assertNotEqual(r.stderr, "")

    def test_json_shape(self):
        r = run(["--json", "--baseline", "3"], "a; b. The flag is set.\n")
        data = json.loads(r.stdout)
        self.assertEqual(set(data), {"findings", "hard", "baseline"})
        self.assertEqual((data["hard"], data["baseline"]), (1, 3))
        self.assertEqual(r.returncode, 0)
        for f in data["findings"]:
            self.assertEqual(set(f), {"file", "line", "col", "rule", "level", "match", "message"})
            self.assertIn(f["level"], ("hard", "advisory"))

    def test_no_bytecode_in_the_skill_folder(self):
        run([], "Short line here.\n")
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(SCRIPT), "__pycache__")))


if __name__ == "__main__":
    unittest.main()
