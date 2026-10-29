"""Shared setup for the ste-lint tests: the module under test and small helpers."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "ste-rewrite", "scripts")
SCRIPT = os.path.join(SCRIPTS, "ste-lint")
sys.dont_write_bytecode = True  # keep __pycache__ out of the skill scripts/ folder
sys.path.insert(0, SCRIPTS)

import ste_rules  # noqa: E402  (needs the path above)

TWENTY = " ".join(["word"] * 20)
BODY26 = " ".join(["word"] * 25) + "."  # 25 words; a marker word would make 26


def lint(text, cap=25):
    return ste_rules.lint(text, "t.md", cap)


def rules(text, rule=None, cap=25):
    return [f for f in lint(text, cap) if rule is None or f["rule"] == rule]


def has(text, rule, cap=25):
    return bool(rules(text, rule, cap))


def run(args, stdin=None):
    return subprocess.run([sys.executable, SCRIPT] + args, input=stdin,
                          capture_output=True, text=True)
