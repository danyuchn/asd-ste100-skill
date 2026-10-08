#!/usr/bin/env python3
"""Install the shared skill for Codex and Claude Code. Python 3.9+, stdlib only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


SKILL_NAME = "asd-ste100"
SOURCE = Path(__file__).resolve().parent.parent
MANIFEST = ".asd-ste100-install.json"
# Explicit payload: never copy a checkout, tests, caches, or another installation.
PAYLOAD = (
    "SKILL.md",
    "LICENSE",
    "agents/openai.yaml",
    "scripts/ste-lint.py",
    "references/writing-rules.md",
    "examples/before-after.md",
    "examples/linter-edge-cases.md",
)
AGENT_DIRS = {"codex": ".agents", "claude-code": ".claude"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    """Describe the whole installed tree, rejecting links and special files."""
    result = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            raise ValueError(f"Refusing to follow installed symlink: {path}")
        if path.is_dir():
            result[relative + "/"] = None
        elif path.is_file():
            if relative != MANIFEST:
                result[relative] = digest(path)
        else:
            raise ValueError(f"Unsupported installed file: {path}")
    return result


def destinations(agent, scope, project_dir):
    agents = AGENT_DIRS if agent == "both" else [agent]
    base = Path.home() if scope == "user" else project_dir.resolve()
    targets = []
    for name in agents:
        config = base / AGENT_DIRS[name]
        if name == "claude-code" and scope == "user":
            config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or config).expanduser()
        targets.append(config.absolute() / "skills" / SKILL_NAME)
    return targets


def preflight(target, action):
    if target.is_symlink():
        raise ValueError(f"{target} is a symlink. Manage it with its original installer.")
    if target.resolve() == SOURCE or target.resolve() in SOURCE.parents:
        raise ValueError(f"Refusing to replace the source checkout: {target}")
    if not target.exists():
        if action == "update":
            raise ValueError(f"{target} is not installed. Run install first.")
        return
    if action == "install":
        raise ValueError(f"{target} already exists. Use update for a managed installation.")
    if not target.is_dir():
        raise ValueError(f"{target} is not a skill directory.")
    manifest = target / MANIFEST
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"{target} was not installed by this script. Use its original installation method.")
    try:
        record = json.loads(manifest.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Invalid installation manifest: {manifest}") from exc
    if not isinstance(record, dict) or record.get("skill") != SKILL_NAME or record.get("format") != 1:
        raise ValueError(f"Unrecognized installation manifest: {manifest}")
    if inventory(target) != record.get("files"):
        raise ValueError(f"{target} has local changes. Back them up and reconcile them before {action}.")


def install(target, action):
    """Stage a complete copy before replacing a managed installation."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".asd-ste100-stage-", dir=target.parent) as temporary:
        stage = Path(temporary) / SKILL_NAME
        stage.mkdir()
        for relative in PAYLOAD:
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / relative, destination)
        record = {"format": 1, "skill": SKILL_NAME, "files": inventory(stage)}
        (stage / MANIFEST).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        # Recheck after staging, before moving anything already installed.
        preflight(target, action)
        backup = Path(temporary) / "previous"
        if target.exists():
            target.rename(backup)
        try:
            stage.rename(target)
        except OSError:
            if backup.exists():
                backup.rename(target)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("action", choices=("install", "update", "uninstall"),
                        help="update and uninstall accept only unmodified copies made by this script")
    parser.add_argument("--agent", choices=("codex", "claude-code", "both"), required=True,
                        help="agent installation directories to manage")
    parser.add_argument("--scope", choices=("project", "user"), default="project",
                        help="install in one project or for this user (default: project)")
    parser.add_argument("--project-dir", type=Path, help="target project (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="validate and show destinations without writing")
    args = parser.parse_args(argv)
    if args.scope == "user" and args.project_dir is not None:
        parser.error("--project-dir applies only to --scope project")
    project = (args.project_dir or Path.cwd()).expanduser()
    if args.scope == "project" and not project.is_dir():
        parser.error(f"project directory does not exist: {project}")
    try:
        if args.action != "uninstall":
            for relative in PAYLOAD:
                if not (SOURCE / relative).is_file():
                    raise ValueError(f"Missing source file: {SOURCE / relative}. Run from a complete repository checkout.")
        targets = destinations(args.agent, args.scope, project)
        # Check every target before changing either agent's installation.
        for target in targets:
            preflight(target, args.action)
        for target in targets:
            if args.dry_run:
                print(f"Would {args.action}: {target}")
            elif args.action == "uninstall":
                preflight(target, args.action)
                if target.exists():
                    shutil.rmtree(target)
                    print(f"Uninstalled: {target}")
                else:
                    print(f"Already absent: {target}")
            else:
                install(target, args.action)
                print(f"{'Installed' if args.action == 'install' else 'Updated'}: {target}")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
