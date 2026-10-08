"""Exercise real copies and CLI calls without touching the user's agent folders."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ste install test ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.codex = self.project / ".agents/skills/asd-ste100"
        self.claude = self.project / ".claude/skills/asd-ste100"

    def run_cli(self, action="install", agent="both", *extra, code=0):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/install.py"), action,
             "--agent", agent, *extra], cwd=self.project,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def test_both_agents_receive_complete_identical_payload(self):
        self.run_cli()
        for target in (self.codex, self.claude):
            for relative in installer.PAYLOAD:
                self.assertEqual((target / relative).read_bytes(), (ROOT / relative).read_bytes())
            self.assertFalse((target / ".git").exists())
            self.assertFalse((target / "tests").exists())
            self.assertFalse((target / "scripts/install.py").exists())
        self.assertEqual(installer.inventory(self.codex), installer.inventory(self.claude))

    def test_individual_agents_and_explicit_project(self):
        self.run_cli("install", "codex", "--project-dir", str(self.project))
        self.assertTrue(self.codex.is_dir())
        self.assertFalse(self.claude.exists())
        self.run_cli(agent="claude-code")
        self.assertTrue(self.claude.is_dir())

    def test_personal_install_and_custom_claude_directory(self):
        personal = self.root / "personal"
        custom_claude = self.root / "custom claude"
        with patch.object(Path, "home", return_value=personal), patch.dict(
            installer.os.environ, {"CLAUDE_CONFIG_DIR": str(custom_claude)}
        ), contextlib.redirect_stdout(io.StringIO()):
            installer.main(["install", "--agent", "both", "--scope", "user"])
            self.assertTrue((personal / ".agents/skills/asd-ste100/SKILL.md").is_file())
            self.assertTrue((custom_claude / "skills/asd-ste100/SKILL.md").is_file())
            installer.main(["uninstall", "--agent", "both", "--scope", "user"])
            self.assertFalse((custom_claude / "skills/asd-ste100").exists())

    def test_dry_run_leaves_no_files(self):
        result = self.run_cli("install", "both", "--dry-run")
        self.assertIn(str(self.codex), result.stdout)
        self.assertIn(str(self.claude), result.stdout)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_collision_is_checked_before_installing_either_agent(self):
        self.claude.mkdir(parents=True)
        note = self.claude / "personal-note.txt"
        note.write_text("Keep this.", encoding="utf-8")
        self.run_cli(code=2)
        self.assertFalse(self.codex.exists())
        self.assertEqual(note.read_text(encoding="utf-8"), "Keep this.")

    def test_dry_run_update_and_uninstall_preserve_installation(self):
        self.run_cli()
        before = installer.inventory(self.codex)
        for action in ("update", "uninstall"):
            self.run_cli(action, "both", "--dry-run")
            self.assertEqual(installer.inventory(self.codex), before)
            self.assertEqual(installer.inventory(self.claude), before)

    def test_update_uses_new_source_and_removes_old_payload(self):
        self.run_cli()
        source = self.root / "new source"
        for relative in installer.PAYLOAD:
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        (source / "SKILL.md").write_text("Updated skill.\n", encoding="utf-8")
        old_example = "examples/linter-edge-cases.md"
        with patch.object(installer, "SOURCE", source), patch.object(
            installer, "PAYLOAD", tuple(p for p in installer.PAYLOAD if p != old_example)
        ), contextlib.redirect_stdout(io.StringIO()):
            installer.main(["update", "--agent", "both", "--project-dir", str(self.project)])
        for target in (self.codex, self.claude):
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "Updated skill.\n")
            self.assertFalse((target / old_example).exists())
        self.run_cli("uninstall")
        self.assertFalse(self.codex.exists())
        self.assertFalse(self.claude.exists())
        self.run_cli("uninstall")  # Removing an absent installation is harmless.

    def test_modified_added_or_deleted_files_block_update_and_removal(self):
        for change in ("edit", "add", "delete", "directory"):
            with self.subTest(change=change):
                self.run_cli()
                before = installer.inventory(self.codex)
                skill = self.claude / "SKILL.md"
                original = skill.read_bytes()
                if change == "edit":
                    skill.write_text("Local edit.", encoding="utf-8")
                elif change == "add":
                    (self.claude / "notes.txt").touch()
                elif change == "delete":
                    skill.unlink()
                else:
                    (self.claude / "notes").mkdir()
                for action in ("update", "uninstall"):
                    result = self.run_cli(action, code=2)
                    self.assertIn("local changes", result.stderr)
                    self.assertEqual(installer.inventory(self.codex), before)
                skill.write_bytes(original)
                if change == "add":
                    (self.claude / "notes.txt").unlink()
                elif change == "directory":
                    (self.claude / "notes").rmdir()
                self.run_cli("uninstall")

    def test_unmanaged_directory_and_invalid_manifest_are_preserved(self):
        self.codex.mkdir(parents=True)
        for manifest in (None, "invalid json", "[]", '{"skill":"another-skill"}'):
            with self.subTest(manifest=manifest):
                if manifest is not None:
                    (self.codex / installer.MANIFEST).write_text(manifest, encoding="utf-8")
                for action in ("update", "uninstall"):
                    self.run_cli(action, "codex", code=2)
                    self.assertTrue(self.codex.is_dir())

    def test_symlink_installation_is_preserved(self):
        self.codex.parent.mkdir(parents=True)
        try:
            self.codex.symlink_to(ROOT, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        for action in ("install", "update", "uninstall"):
            self.run_cli(action, "codex", code=2)
            self.assertTrue(self.codex.is_symlink())
            self.assertTrue((ROOT / "SKILL.md").is_file())

    def test_failed_replacement_restores_previous_installation(self):
        self.run_cli()
        before = installer.inventory(self.codex)
        original_rename = Path.rename

        def fail_stage(path, destination):
            if path.parent.name.startswith(".asd-ste100-stage-"):
                if path.name == installer.SKILL_NAME:
                    raise OSError("Simulated rename failure")
            return original_rename(path, destination)

        with patch.object(Path, "rename", fail_stage), self.assertRaises(OSError):
            installer.install(self.codex, "update")
        self.assertEqual(installer.inventory(self.codex), before)
        self.assertFalse(list(self.codex.parent.glob(".asd-ste100-stage-*")))

    def test_failed_copy_preserves_previous_installation(self):
        self.run_cli()
        before = installer.inventory(self.codex)
        with patch.object(installer.shutil, "copy2", side_effect=OSError("Disk full")):
            with self.assertRaises(OSError):
                installer.install(self.codex, "update")
        self.assertEqual(installer.inventory(self.codex), before)
        self.assertFalse(list(self.codex.parent.glob(".asd-ste100-stage-*")))

    def test_installed_linter_works_outside_source_and_install_directory(self):
        self.run_cli()
        document = self.project / "input text.md"
        document.write_text("The request may have failed.\n", encoding="utf-8")
        for target in (self.codex, self.claude):
            result = subprocess.run(
                [sys.executable, str(target / "scripts/ste-lint.py"), "--json", str(document)],
                cwd=self.root, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["violations"], [])

    def test_invalid_cli_and_missing_installation(self):
        self.run_cli("update", code=2)
        self.run_cli("install", "codex", "--scope", "user", "--project-dir", str(self.project), code=2)
        self.run_cli("install", "codex", "--project-dir", str(self.root / "missing"), code=2)
        self.run_cli("install", "codex", "--scop", "user", code=2)


if __name__ == "__main__":
    unittest.main()
