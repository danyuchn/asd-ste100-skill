"""Validate the portable skill contract and linter integration."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_frontmatter_uses_portable_fields(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match)
        metadata = yaml.safe_load(match.group(1))
        self.assertEqual(metadata["name"], "asd-ste100")
        self.assertTrue(set(metadata) <= {"name", "description", "license", "metadata", "compatibility", "allowed-tools"})
        self.assertTrue(1 <= len(metadata["description"]) <= 1024)
        self.assertEqual(metadata["license"], "MIT")
        self.assertRegex(metadata["metadata"]["version"], r"^\d+\.\d+\.\d+$")
        self.assertNotIn("version", metadata)

    def test_codex_metadata_matches_shared_skill(self):
        metadata = yaml.safe_load((ROOT / "agents/openai.yaml").read_text(encoding="utf-8"))
        interface = metadata["interface"]
        self.assertTrue(interface["display_name"])
        self.assertTrue(25 <= len(interface["short_description"]) <= 64)
        self.assertIn("$asd-ste100", interface["default_prompt"])
        self.assertTrue(metadata.get("policy", {}).get("allow_implicit_invocation", True))

    def test_referenced_resources_exist(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        resources = re.findall(r"`((?:scripts|references|examples)/[^`]+)`", text)
        self.assertTrue(resources)
        for relative in resources:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).exists())

    def lint(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/ste-lint.py"), *args],
                              cwd=ROOT, capture_output=True, text=True)

    def test_selftest(self):
        result = self.lint("--selftest")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_readme_baseline_matches_current_skill(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        baseline = re.search(r"--baseline (\d+) SKILL.md", readme).group(1)
        result = self.lint("--json", "--baseline", baseline, "SKILL.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["hard_count"], int(baseline))

    def test_edge_case_fixture(self):
        result = self.lint("--json", "examples/linter-edge-cases.md")
        self.assertEqual(result.returncode, 1)
        findings = json.loads(result.stdout)["violations"]
        self.assertEqual([f["rule"] for f in findings], ["dangling-conjunction"] * 2)


if __name__ == "__main__":
    unittest.main()
