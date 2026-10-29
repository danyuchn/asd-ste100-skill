# ASD-STE100 Rewrite: Simplified Technical English for Agent Output

A Claude Code plugin that rewrites dense, ambiguous English in the style of [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/) (STE). The aerospace and defense industry made this controlled language so that a maintenance instruction has only one reading.

The plugin applies the same discipline to a different reader: a model or a program. That reader parses a tool description, an error message, a system prompt, or an instruction from another agent. It has no human to ask what the author meant.

> [!IMPORTANT]
> This project has no affiliation with ASD or the STEMG, and they do not endorse it. Simplified Technical English and ASD-STE100 are a copyright and a trademark of ASD, Brussels, Belgium (European Union Trade Mark No. 017966390). The STEMG [white paper on STE and AI](https://www.asd-ste100.org/assets/files/WhitePaper-ASD-STE100_and_AI.pdf) (June 2026) states that the STEMG does not endorse AI tools. Output of this plugin is AI-assisted text in the STE style. No process certifies it as STE.

## Why STE for Agents

STE exists because a misread instruction on an aircraft can kill people. Many of its readers were not native English speakers, and they had no author to call. The fix of the standard: one meaning per word, active voice, simple tenses, one instruction per sentence, short sentences, and no dropped words.

A model that reads the output of another model is in the same position. It has no way to ask "did you mean X or Y?" The rules that stop a mechanic from misreading a torque value also stop an agent from misreading a tool description.

## Before / After

| Before | After |
| --- | --- |
| "This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review." | "The tool tries to synchronize state across the configured backends. If it finds a conflict, it may resolve the conflict automatically, depending on the configured strategy. If the tool does not resolve the conflict, it reports the conflict for manual review." |
| "An error may have occurred while processing your request due to a possible mismatch in the expected data format, which could be caused by an outdated client version." | "An error may have occurred during your request. The cause may be a data format that does not match the expected format. An outdated client version could cause this mismatch." |

Each hedge stays. "May have occurred" becomes "may have failed", not "failed". A rewrite that turns a hedge into a fact, or adds a cause, makes a different claim.

## Install

With the skills CLI:

```bash
bunx skills add danyuchn/asd-ste100-skill
```

With a clone and a copy of the skill folder. Claude Code loads a personal skill from `~/.claude/skills/<name>/SKILL.md`, so the copy must be the skill folder itself:

```bash
git clone https://github.com/danyuchn/asd-ste100-skill
cp -R asd-ste100-skill/skills/ste-rewrite ~/.claude/skills/
```

As a Claude Code plugin:

```bash
claude plugin marketplace add danyuchn/asd-ste100-skill
claude plugin install asd-ste100@asd-ste100-skill
```

To try a local checkout for one session, run `claude --plugin-dir .` in the repository.

The skill folder `skills/ste-rewrite/` is self-contained. An install of the skill alone copies only `SKILL.md`, `references/`, and `scripts/`.

The linter needs `python3` 3.9 or later on the `PATH`. It uses the standard library only.

## Usage

Ask in plain words, or start the skill by name:

```text
Disambiguate this tool description: ...
Rewrite this error message so that an agent cannot misread it: ...
Apply STE100 to docs/runbook.md
/asd-ste100:ste-rewrite <text or file>
```

You get the rewritten text and nothing else. When the skill keeps a longer phrase on purpose, it adds a `Kept as-is:` line. For a file, it edits the file. To see the rules that it applied, add "show the diff" or "which rules did it break" to the request.

The skill picks a mode from the text type. Strict covers procedures, error messages, tool descriptions, prompts, and instructions to agents. Flavored covers READMEs, PR descriptions, and changelogs. The rules of each mode, with the word caps, are in [`skills/ste-rewrite/SKILL.md`](skills/ste-rewrite/SKILL.md).

## What Is in the Plugin

| Path | Content |
| --- | --- |
| `skills/ste-rewrite/SKILL.md` | The skill: rules, process, output format, and examples. Claude loads it when a request matches its `description` or its `when_to_use`. |
| `skills/ste-rewrite/references/examples.md` | Eight examples with their mode and the reason for each change. Claude reads the file only for a tool description or Flavored prose. |
| `skills/ste-rewrite/references/writing-rules.md` | The rule summary and its citations. Claude reads the file on request. |
| `skills/ste-rewrite/scripts/ste-lint` | The command line of the linter. The skill runs it by its path in the installed plugin, with no permission prompt. |
| `skills/ste-rewrite/scripts/ste_*.py` | The parts of the linter: `ste_rules` the rules, `ste_words` the word lists, `ste_blocks` the document structure, `ste_tables` the tables, `ste_text` the sentences and the masking. |
| `evals/` | Cases for `claude plugin eval` and trigger queries for the skill description. Not loaded at run time. |
| `evals/SOURCES.md` | The source of each eval input that comes from captured Claude Code prompt text. |
| `evals/compare-runs.py` | Compares two eval runs case by case, and marks each case that a change fixed or broke. |
| `evals/LESSONS.md` | What the measured runs taught about the way a Claude model reads this skill. Each lesson states its numbers. |
| `tests/` | Unit tests for the linter. |
| `justfile` | The commands of the repo: the checks, the eval matrix, and the install. `just --list` prints them. |

## The Linter

`ste-lint` checks the structural rules that need no dictionary. It reads files, or stdin when you give no file. It skips front matter, code, HTML, and link URLs, and treats each table cell as its own text.

```bash
skills/ste-rewrite/scripts/ste-lint README.md
skills/ste-rewrite/scripts/ste-lint --max-words 20 <<'EOF'
Text to check.
EOF
skills/ste-rewrite/scripts/ste-lint --json --baseline 5 docs/*.md
```

| Rule | Level | Finds |
| --- | --- | --- |
| `semicolon` | hard | Any semicolon (Rule 8.1) |
| `long-sentence` | hard | A sentence over `--max-words` (default 25) |
| `phrasal-verb` | hard | `spin up`, `reach out`, `dive into`, `kick off`, `circle back`, `touch base` |
| `marketing-adjective` | hard | `seamless`, `robust`, `cutting-edge`, `effortless`, `blazing-fast`, `world-class`, `state-of-the-art`, `game-changing` |
| `nominalization` | hard | `perform an analysis`, `conduct a review`, `carry out an inspection` |
| `synonym-rotation` | hard | Two words of one group in one file, such as `check` and `verify` |
| `dangling-conjunction` | hard | A list item that ends with "and" or "or" |
| `invisible-character` | hard | `U+00A0`, `U+200B`, `U+FEFF`: a character that prints as nothing. A model cannot see it. |
| `mixed-script-word` | hard | A word of two scripts, such as a Cyrillic letter in a Latin word. A model cannot see it. |
| `passive-voice` | advisory | A possible passive |
| `present-perfect` | advisory | A compound tense, except after a modal ("may have failed") |

Flags: `--json`, `--baseline N` (pass unless hard findings exceed N, default 0), `--disable RULES`, `--max-words N` (default 25), and `--limit N` (text output only, default 50, 0 for all). Exit codes: 0 pass, 1 hard findings over the baseline, 2 usage error. `ste-lint --help` lists the details. A text output line has the form `file:line:col: rule: message [match]`, so an editor can parse it.

The linter never flags hedges or modality, because confidence is content. It does not check noun clusters, one instruction per sentence, phrasal verbs outside its list ("take off the panel" passes), or meaning. It does not compare a rewrite with its source. Zero findings means that these checks found nothing, not that the text follows STE.

## Development

The repo lints its own prose with the skill. A pattern that the rules forbid sits in a code span, and the linter masks a code span. Each baseline therefore stays at the real count, and a new finding fails the run. Two baselines remain: `README.md` keeps the two Before sentences of the table above, and `references/writing-rules.md` quotes the text of Rule 8.1, which contains a semicolon.

The `justfile` holds each command. `just --list` prints all of them.

```bash
just check          # the free checks: test, lint, types, validate
just test           # the linter tests
just lint           # lint the prose of the repo with the skill
just lint-one FILE  # lint one file or text
just types          # type check the scripts and the tests with zuban
just validate       # check the manifests and the layout
just eval MODEL     # the eval cases on one model: paid model runs
just eval-matrix    # the eval cases on each model of the matrix: paid model runs
just eval-case MODEL CASE   # one eval case on one model: paid model runs
just compare BEFORE AFTER   # compare two eval runs case by case
just triggers 3 validation  # the trigger rate of the description: paid model runs
just fire-rate 3    # how often the skill fires on the eval prompts: paid model runs
just install        # install the plugin from the marketplace
```

`just --dry-run <recipe>` prints the commands of a recipe, so you can run them without `just`.

`claude plugin eval` runs each case in `evals/<case>/` and scores the graders. It exits 1 when a case scores below `--threshold` (default 1.0), and `--no-publish` keeps the HTML report local. `just eval` passes `--ablation none`, which runs the plugin arm only and halves the paid runs. It also passes `--max-cost-usd`, which stops one model at its ceiling, and `--judge-model claude-sonnet-5-5`: the default judge is Haiku, and it voted against correct answers.

`--ablation with-without` runs each case twice, with the plugin and without it, and reports the delta. It is the default of the command whenever a plugin resolves. `just eval-matrix` runs the suite on Haiku 5.5, Sonnet 5.5, and Opus 5.5, because a skill must work on each model that reads it. `evals/trigger-queries.sh` runs each query in `evals/trigger-queries.json` and prints how often the skill triggered. It takes the rounds, the split, and the model. `just triggers` passes Haiku 5.5, because the weakest model of the matrix misses the most triggers. Change the description with the `train` queries, and judge the change with the `validation` queries, as the [Agent Skills guide](https://agentskills.io/skill-creation/optimizing-descriptions) recommends.

The split only works when the trigger text avoids the validation queries. The current `when_to_use` names a system prompt and a README, and both words appear in the validation queries alone. Two of the four positive validation queries therefore measure the fit, not the generalization. The other two give the clean signal: the `disambiguate` query went from 0 of 3 to 3 of 3. The `status report` query stayed at 0 of 3. Each of the four negative queries stayed at 0 of 3, so the longer text added no false trigger.

Two different caps limit the trigger text, so the skill splits it across two keys. The plugin directory accepts a `description` of at most 200 characters, and `claude plugin validate` reports a longer one. Claude Code instead caps `description` and `when_to_use` together at 1,536 characters for one entry (`skillListingMaxDescChars`). The `description` therefore stays under 200 characters for the catalog, and `when_to_use` carries the rest of the trigger text. The two together come to 904 characters.

One further limit applies at run time. The whole skill listing gets 1 percent of the context window, counted at 3 characters per token for the 5.5 models. An Opus 5.5 session with a 200,000-token window gives about 6,000 characters to every installed skill together. When the listing passes that budget, Claude Code drops the descriptions and keeps only the names. This entry uses about 15 percent of that budget, so a long `when_to_use` costs a user who installs many skills. The trigger scripts pass `--setting-sources project`, which lists this skill alone, so a measured trigger rate does not cover this risk.

`evals/fire-rate.sh` prints how often the skill fired on each eval prompt. It takes the rounds, the model, and one case name. An eval pass samples the skill choice once per case, and it pays a judge for each grader. This script samples the choice alone, so a description change gets more samples for a small part of the price. The choice of a skill varies from run to run. Two descriptions that share a clause gave 3 of 3 and 0 of 3 on one query, so one sample decides nothing.

The suite is hard on purpose. The matrix of 2026-10-29 ran at `medium` effort with three runs for each case. A case counts as a pass only when all three runs pass every grader. Haiku 5.5 passed 5 of the 17 cases, Sonnet 5.5 passed 14, and Opus 5.5 passed 14. The mean scores were 0.916, 0.990, and 0.994. Four earlier matrices with one run for each case reported 11 to 13 for Haiku. One run therefore finds about half of the Haiku misses. The fire rate on Haiku 5.5 is 47 of 48 want-yes runs, and the should-not-fire case stays at 0 of 3. The JSON of every run stays local, because `.gitignore` holds `evals/results/`.

Six fixes followed that matrix, and each one carries a measurement of three runs for the case. On Haiku 5.5, `cc-system-prompt-permissions` went from 0 of 3 to 2 of 3. `invisible-space` went from 0 of 3 to 2 of 3, and `injection-in-source` went from 1 of 3 to 3 of 3. On Opus 5.5, `cc-system-prompt-permissions`, `cc-tool-schema-effort`, and `injection-in-source` each reached 3 of 3 at 1.00. Two of the six fixes are graders that judged two concerns at once, and four are rules of the skill. `evals/LESSONS.md` holds the evidence for each one, and it holds the changes that the measurement rejected.

Most of what the matrix caught is a real shortcut. It found a 23-word sentence against a 20-word cap, a kept `times out`, a `Kept as-is` reason that claims more than the source, and an added prohibition. Treat a case that passes on one model and fails on another as a finding about the model, not a defect of the case. `evals/LESSONS.md` records each change that the runs accepted, and each change that they rejected.

A grader is deterministic whenever a pattern can decide its question. A model judge then gets only the questions about meaning. The cases with the `adversarial` tag test the shortcuts that a model takes. It obeys an instruction inside the text that it must rewrite. It strips the semicolon inside a code span. It drops a hedge to meet the word cap. It rewrites text that already follows the rules. It copies an invisible character that it cannot see. No model and no judge can read U+00A0 or a Cyrillic letter in a Latin word. The linter reads the Cyrillic letter, so that case needs the linter. The linter never reads the invisible character, because Claude Code refuses a `Bash` command that holds one. The refusal is itself the finding, and the skill reads it that way.

[zuban](https://github.com/zubanls/zuban) is a type checker and a language server for Python, under AGPL-3.0 with a commercial option. It states no lint rules, so it checks types only. `uvx` runs it without an install (`brew install uv` gives `uvx`), and `pip install zuban` installs it. `MYPYPATH` must point at the scripts folder, because the scripts import each other through `sys.path` at run time. `scripts/ste-lint` needs its own path argument, because zuban finds only the files that end in `.py`. The scripts carry no type annotations, so `--strict` reports each missing annotation.

## Scope and Limits

Built for agent messages, tool and function descriptions, error messages, system prompts, and technical prose that a model or a non-native reader must parse alone. Not built for creative or persuasive writing, where voice is the point.

The plugin fixes the form of a text, not its content. A paragraph that says nothing comes out short, clean, and still empty.

It does not include the STE dictionary of about 900 approved words. ASD-STE100 is free to download but not free to redistribute. Issue 9 permits reproduction only with the written authority of ASD, or for listed categories of organizations. This project is not in those categories. So the skill applies the principle (the plainest common word, used the same way each time) and does not check words against the list. For certified STE documentation, [request the standard](https://www.asd-ste100.org/STE_downloads.html) and check each word against its dictionary.

## Other Languages

- **Hebrew:** [g4lb/asd-ste100-hebrew-skill](https://github.com/g4lb/asd-ste100-hebrew-skill) is a Hebrew port of the upstream skill, with a Hebrew linter. ASD-STE100 defines English only, so the Hebrew rules are an adaptation, not an official standard.

## Optional: A Local Translation Model

STE exists so that a translator, human or machine, has one reading of each sentence. If you translate the rewrite, you can run [google/translategemma-4b-it](https://huggingface.co/google/translategemma-4b-it) on your own hardware. It is a Gemma 3 model of 4B parameters for translation between 55 languages. The plugin does not call it, and the model does not check STE. Use the skill first, then translate the result.

- Google gates the weights. Accept the [Gemma terms](https://ai.google.dev/gemma/terms) on the model page, then authenticate with your Hugging Face account.
- The input limit is 2K tokens, so send one section or one paragraph at a time.
- `docker model run hf.co/google/translategemma-4b-it` is the shortest path. Transformers (`AutoProcessor` with `AutoModelForImageTextToText`), vLLM, and SGLang also serve it, and the community publishes quantized builds for llama.cpp, Ollama, and LM Studio.
- A 4B model in a quantized build runs on a recent laptop. Measure the memory and the speed on your own machine, because the model card gives no number for it.

## Related Tools

- [meiluosi/rewrite-fidelity-skill](https://github.com/meiluosi/rewrite-fidelity-skill) compares the original text with the rewrite and flags changes in meaning and modality. It uses pattern matching, so check each flag yourself.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/), with the trademark notice (EUTM No. 017966390)
- [ASD-STE100: About STE](https://www.asd-ste100.org/about_STE.html)
- [STEMG white paper: ASD-STE100 and AI](https://www.asd-ste100.org/assets/files/WhitePaper-ASD-STE100_and_AI.pdf)
- [ASD Europe: Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English on Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe: ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)
- [SKYbrary: Simplified Technical English](https://skybrary.aero/articles/simplified-technical-english-ste)

## License

MIT. See [LICENSE](LICENSE).
