# ASD-STE100 for Claude Code and Codex

An [Agent Skill](https://agentskills.io) for **Claude Code and OpenAI Codex** that rewrites dense, ambiguous English using [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/) principles. It preserves facts, conditions, and uncertainty while making technical text easier to read.

Both agents use the same `SKILL.md`, references, examples, and optional Python linter. The installed skill name is **`asd-ste100`**. The repository name is `asd-ste100-skill`.

```bash
# Install for both agents in your current project (requires Node.js/npx)
npx skills add danyuchn/asd-ste100-skill --skill asd-ste100 --agent codex claude-code
```

Use `$asd-ste100` in Codex or `/asd-ste100` in Claude Code. See [installation](#installation) for personal installations and a Python alternative that needs no Node.js.

This skill repurposes that same discipline for a different reader: an **AI agent** parsing another agent's output, a tool description, an error message, or an inter-agent instruction, with no human in the loop to resolve ambiguity.

## Why STE, and Why for Agents

STE exists because a misread instruction on an aircraft can kill people, and the intended readers were often not native English speakers with no author to call for clarification. The standard's fix: one meaning per word, active voice, simple tenses, one instruction per sentence, short sentences, no dropped words.

An LLM agent parsing another agent's output is in a strikingly similar position — no back-channel, no way to ask "did you mean X or Y?" The same rules that keep a mechanic from misreading a torque spec keep a downstream agent from misreading a tool description or an inter-agent message.

## Before / After

| Before | After |
|---|---|
| "This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review." | "The tool tries to synchronize state across the configured backends. If it finds a conflict, it reads the configured strategy. If the strategy allows automatic resolution, the tool may resolve the conflict without a user. If the tool does not resolve the conflict, it reports the conflict for manual review." |
| "An error may have occurred while processing your request due to a possible mismatch in the expected data format, which could be caused by an outdated client version." | "Your request may have failed. The cause may be a data format that does not match what the server expects. An outdated client can cause this mismatch. Check your client version." |

More examples, including illustrations of the official STE rules themselves, in [`examples/before-after.md`](examples/before-after.md).

## What This Skill Does

1. Picks a mode. **Strict** covers procedures, error messages, and tool descriptions. **STE-flavored** covers READMEs, PR descriptions, and explanatory prose. STE-flavored keeps the sentence discipline but not the fixed-vocabulary lockdown.
2. Reads the input English text for meaning.
3. Flags every rule violation sentence-by-sentence: ambiguous word choice, present-perfect/complex tense, passive voice with an unclear actor, multi-instruction sentences, oversized noun clusters, dropped words, sentences over length, phrasal verbs, nominalized actions, semicolons, hedge stacks, and marketing adjectives.
4. Rewrites each flagged sentence — without dropping any fact, condition, or scope qualifier from the original. If a shorter phrasing would lose required precision, it keeps the longer phrasing and flags the trade-off instead of silently simplifying.
5. Outputs the rewritten text on its own — no preamble, no mode announcement, no change summary — plus a one-line `Kept as-is:` note when it deliberately left something unsimplified.

Ask for the reasoning ("show the diff", "which rules did it break") and it outputs a before/after table naming each rule instead.

The structural rules it checks are mechanical — you can point at the word or punctuation mark that breaks each one. The rules that depend on ASD's dictionary are flagged as advisory rather than enforced, and the rules that need taste are left to you.

The linter checks structural patterns only. It does not compare an original text with a rewrite, verify that requirement strength stayed the same, or prove that the rewrite preserved meaning. A zero-violation result means that the configured structural checks found no problems.

The deterministic linter checks semicolons, a short list of soft phrasal verbs (spin up, reach out, dive into, kick off, circle back, touch base), nominalizations, marketing adjectives, passive voice, present-perfect forms (including irregular participles such as "has run"), long sentences, synonym rotation, and dangling conjunctions in supported list items. It does not check noun-cluster length (that needs part-of-speech tagging) and it does not know phrasal verbs outside its list, so "take off the panel" passes. It never flags hedges or modality.

The repo's own prose does not lint clean: the rule tables quote the patterns they forbid, and some sentences run long. Lint it with `python3 scripts/ste-lint.py --baseline 40 SKILL.md` and read the findings as examples, not defects.

The dangling-conjunction rule checks list markers at the start of a line with zero to three leading spaces and ASCII spaces after the marker. It supports unordered markers `-`, `*`, and `+`, and ordered numeric markers that end in `.` or `)`, such as `1.` or `1)`. It checks indented continuation lines up to the final meaningful line. It does not parse list syntax inside blockquotes, lazy continuation, or full nested-list semantics. A standalone line with four or more leading spaces is not treated as a list marker. Within an active list item, indentation at the computed content column is treated as continuation text. Fence detection follows the linter's existing simple rule: a stripped line beginning with three backticks or three tildes toggles the fence state.

The intentionally invalid [edge-case fixture](examples/linter-edge-cases.md) demonstrates incomplete Markdown list items. Run `python3 scripts/ste-lint.py examples/linter-edge-cases.md` to confirm that the linter reports the two expected findings. The file is a test fixture and should not be used as compliant STE prose.

It does **not** reproduce ASD's official ~900-word approved dictionary. The standard is free to obtain but not free to redistribute: Issue 9 permits reproduction only with ASD's written authority, or by eight listed categories of organisation that this project does not belong to. This skill applies the underlying *principle* (plainest available word, used the same way every time) rather than checking against a fixed word list. For certified STE-compliant documentation, use the real standard.

Full rule summary and citations: [`references/writing-rules.md`](references/writing-rules.md).

## Installation

Choose one installation method per scope to avoid duplicate skills. Install in the project where you want to use the skill, or choose a personal installation for all projects on this machine.

| Agent | Project directory | Personal directory | Explicit invocation |
|---|---|---|---|
| Codex | `.agents/skills/asd-ste100/` | `~/.agents/skills/asd-ste100/` | `$asd-ste100` |
| Claude Code | `.claude/skills/asd-ste100/` | `~/.claude/skills/asd-ste100/` | `/asd-ste100` |

These locations follow the [Codex skill documentation](https://developers.openai.com/codex/skills/) and [Claude Code skill documentation](https://code.claude.com/docs/en/skills). Both agents can also select the skill when a request matches its description.

### Quick install with the skills CLI

Requires Node.js and `npx`. Run from your target project's root:

```bash
# Both agents
npx skills add danyuchn/asd-ste100-skill --skill asd-ste100 --agent codex claude-code

# Or choose one
npx skills add danyuchn/asd-ste100-skill --skill asd-ste100 --agent codex
npx skills add danyuchn/asd-ste100-skill --skill asd-ste100 --agent claude-code

# Personal installation for all your projects
npx skills add danyuchn/asd-ste100-skill --skill asd-ste100 --agent codex claude-code --global
```

The third-party [skills CLI](https://github.com/vercel-labs/skills) manages discovery and installation. It supports symlinks and copies (`--copy`), and `--yes` skips its prompts. See its documentation for telemetry controls and other options.

### Install from a checkout with Python

Requires Git to clone and **Python 3.9+** to install. No Node.js, pip packages, API keys, or network access are needed after cloning.

```bash
git clone https://github.com/danyuchn/asd-ste100-skill.git
cd asd-ste100-skill

# Copy into both agents' directories in an existing project
python3 scripts/install.py install --agent both --project-dir /path/to/your/project

# Or install for all your projects
python3 scripts/install.py install --agent both --scope user
```

Use `--agent codex` or `--agent claude-code` for one agent. Project scope is the default, and its default target is your current directory. Add `--dry-run` to preview destinations without writing files. On Windows, use `py -3` if `python3` is unavailable.

The installer copies the shared skill, Codex UI metadata, linter, references, examples, and license. It excludes Git history and development files. Each installation is independent of the checkout and includes a manifest for updates and removal. `install` never overwrites an existing destination.

Personal Claude Code installations honor `CLAUDE_CONFIG_DIR` when set. Codex uses the documented `~/.agents/skills` location. The installer does not change agent settings or permissions.

### Manual Git installation

For a personal installation that you maintain with Git, clone directly into the agent's skills directory. These commands are for macOS, Linux, or WSL:

```bash
# Codex
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/danyuchn/asd-ste100-skill.git "$HOME/.agents/skills/asd-ste100"

# Claude Code
mkdir -p "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
git clone https://github.com/danyuchn/asd-ste100-skill.git "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/asd-ste100"
```

Keep the full repository so the linter and references remain available. Cloning next to your project, or copying only `SKILL.md`, is not a complete installation.

### Verify discovery

In Codex CLI or the IDE extension, type `$asd-ste100` or open `/skills`. In the desktop app, select the skill from the skill picker. In Claude Code, type `/asd-ste100`. Restart the agent if a new installation does not appear.

Try simplifying “An error may have occurred while processing your request due to a possible mismatch in the expected data format.” The result should preserve uncertainty, for example: “Your request may have failed. The data format might not match the expected format.” Wording can vary between agents and models.

### Update or uninstall

Use the method that created the installation:

| Method | Update | Uninstall |
|---|---|---|
| skills CLI | `npx skills update asd-ste100` (select the scope) | `npx skills remove asd-ste100` (select the agents; add `--global` for personal scope) |
| Python installer | Pull the source checkout, then use `update` below | Use `uninstall` below |
| Git clone | `git -C /path/to/installed/asd-ste100 pull --ff-only` | Back up local edits, then remove that clone directory |

For Python-managed installations, run from the source checkout:

```bash
# Update a project installation
git pull --ff-only
python3 scripts/install.py update --agent both --project-dir /path/to/your/project

# Remove it when no longer needed
python3 scripts/install.py uninstall --agent both --project-dir /path/to/your/project
```

For personal installations, replace `--project-dir ...` with `--scope user`. Add `--dry-run` to preview either operation.

Updates and removal stop if installed files were edited, added, or deleted. Back up and reconcile those changes first. The script refuses to manage symlinks, manual clones, or installations from another installer. It checks both destinations before starting a `--agent both` operation. Each update is staged separately; an operating-system error can still leave one agent updated and the other unchanged. Printed paths identify completed operations.

Existing Claude Code users can keep their installation and add only Codex. `/asd-ste100` keeps its name. Avoid duplicate copies in directories scanned by the same agent.

## Usage

In Codex:

```text
$asd-ste100 Rewrite this tool description so another agent cannot misread it: ...
```

In Claude Code:

```text
/asd-ste100 Rewrite this tool description so another agent cannot misread it: ...
```

Or ask either agent to simplify or clarify English text:

```
Disambiguate this tool description
Rewrite this error message so an agent can't misparse it
Apply ASD-STE100 to this instruction
```

The same instructions apply in both agents. The skill resolves its scripts and references relative to the installed `SKILL.md`, so your working directory can be elsewhere. It preserves identifiers, code, placeholders, URLs, and command syntax unless you ask to change them.

You get the rewritten text back and nothing else. To see which rules were applied, add "show the diff" or "explain the changes" to the request.

## Optional linter

Rewriting needs only the agent and the skill files. The linter needs **Python 3.9+** and the standard library. It works with either agent or by itself.

From this checkout:

```bash
python3 scripts/ste-lint.py path/to/document.md
python3 scripts/ste-lint.py --json path/to/document.md
python3 scripts/ste-lint.py --baseline 5 path/to/document.md
python3 scripts/ste-lint.py --disable passive-voice,present-perfect path/to/document.md
```

With no file arguments it reads stdin. From another directory, use the installed script's absolute path:

```bash
# Personal Codex installation
python3 "$HOME/.agents/skills/asd-ste100/scripts/ste-lint.py" ./README.md

# Personal Claude Code installation
python3 "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/asd-ste100/scripts/ste-lint.py" ./README.md
```

| Exit code | Meaning |
|---|---|
| `0` | Hard findings do not exceed the baseline |
| `1` | Hard findings exceed the baseline |

The general sentence cap is 25 words; the linter does not separately enforce the skill's 20-word procedural limit. A clean run cannot prove meaning preservation or dictionary compliance.

## Development

The repository root is the canonical skill package. Maintain one copy of its instructions and resources for both agents. Codex display metadata lives in `agents/openai.yaml`. The shared frontmatter uses standard Agent Skills fields, with the version under `metadata.version`.

```text
SKILL.md                     Shared instructions and discovery metadata
agents/openai.yaml           Codex display name and suggested prompt
scripts/ste-lint.py          Optional standalone linter
scripts/install.py           Installer, updater, and uninstaller
references/writing-rules.md  Rule details and citations
examples/                    Worked rewrites and linter fixture
tests/                       Package and installer regression tests
```

Create a virtual environment and activate it before installing development dependencies:

```bash
python3 -m venv .venv
# macOS/Linux:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
python3 scripts/ste-lint.py --selftest
```

PyYAML is needed only to validate development metadata. Tests use temporary projects and home directories. They cover both agents, installation, update, removal, conflicts, paths with spaces, and the installed linter. GitHub Actions runs the checks on Linux, macOS, and Windows.

## Scope

Built for: agent-to-agent messages, tool/function descriptions, error messages, system prompts, inter-agent instructions — any English text a machine or non-native reader has to parse without a human to ask.

Not built for: creative writing, marketing copy, or anything where voice and nuance are the point — STE is deliberately flat and literal by design.

One limit worth stating up front: this fixes the form of a text, not its substance. A paragraph with nothing to say comes out short, clean, and still empty.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/)
- [ASD-STE100 — About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe — Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English — Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe — ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)

## License

MIT — see [LICENSE](LICENSE).
