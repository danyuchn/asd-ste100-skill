# ASD-STE100 Skill — Simplified Technical English

A Claude Code skill for English that a reader must not misread. It applies [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/) (STE), the controlled-language standard the aerospace and defense industry built so aircraft maintenance instructions cannot be misread. The reader here is anyone who cannot ask you a question. That is an AI agent parsing a tool description, or a colleague reading your design doc months later.

STE is an authoring standard, not a cleanup tool. Use this skill to write the first draft. Use it again to revise a draft that exists.

## Two Paths

| | Write | Revise |
|---|---|---|
| Input | None. You produce the text. | An existing text. |
| Trigger | "Write the PR description." "Write this error message." | "Rewrite this." "Disambiguate this." |
| Process | Apply the rules as you write, then scan your own draft. | Flag each violation, then fix it without changing what the text says. |
| Hazard | You assert what you never checked. | You lose a fact, or you weaken a hedge the source stated. |
| Output | The text alone. No diff exists. | The text alone, or a rule table on request. |

The rules are the same on both paths. Only the process and the hazard change.

Each path picks a mode. **Strict** for procedures, error messages, and tool descriptions. **STE-flavored** for READMEs, PR descriptions, and explanatory prose, which keeps the sentence discipline but not the fixed-vocabulary lockdown.

Worked examples: [`examples/before-after.md`](examples/before-after.md). Full rule summary and sources: [`references/writing-rules.md`](references/writing-rules.md).

## Install

```bash
git clone https://github.com/ahmed-irfan/asd-ste100-skill ~/.claude/skills/asd-ste100
```

## Usage

Name the artifact to write it:

```
Write the PR description for this branch
Write the error message for a failed schema load
```

Name the fix to revise it:

```
Disambiguate this tool description
Apply ASD-STE100 to this instruction
```

You get the text back and nothing else. On the revise path, add "show the diff" to see which rules applied.

To make the write path automatic, add this to your `CLAUDE.md`:

```markdown
Invoke the asd-ste100 skill before you write a PR description, a commit
message, an issue body, a design doc, a plan, a code review comment, or a
docstring. Do not wait to be asked.
```

## Limits

This skill does not reproduce ASD's official ~900-word approved dictionary. The standard is free to obtain but not free to redistribute. It applies the underlying principle instead: pick the plainest available word, and use it the same way every time. For certified STE documentation, use the real standard.

STE fixes the form of a text, not its substance. A paragraph with nothing to say comes out short, clean, and still empty. On the write path that limit bites harder, because a clean sentence reads as a checked one.

Not for creative or marketing copy. STE is flat and literal by design.

## License

MIT — see [LICENSE](LICENSE).
