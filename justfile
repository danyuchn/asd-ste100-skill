skill := "skills/ste-rewrite"
lint := skill / "scripts/ste-lint"
scripts := skill / "scripts"

# Baselines: the hard findings that each file keeps on purpose. README.md holds the
# two Before sentences of the Before and After table, and the rule summary quotes
# Rule 8.1 with its semicolon. Each other pattern sits in a code span, which the
# linter masks, so the baseline stays at the real count and a new finding fails.
readme_baseline := "2"
skill_baseline := "0"
rules_baseline := "1"

plugin := "asd-ste100"
marketplace := "danyuchn/asd-ste100-skill"

# The eval matrix. Each model runs at this effort, because CLAUDE_CODE_EFFORT_LEVEL
# wins over --effort and the settings.
effort := "medium"
models := "claude-haiku-5-5 claude-sonnet-5-5 claude-opus-5-5"
# Each run is a full claude child on one credential, so they share one rate limit.
concurrency := "4"
# The default judge is haiku. It voted 3-0 against correct answers in the first
# matrix run, so the suite pays for a stronger judge.
judge := "claude-sonnet-5-5"
# A ceiling for one model of the matrix. The command exits 2 when it hits this.
# One model at 3 runs for each case costs more, so raise it on the command line:
# just max_cost=12 out=evals/results/v14 eval-matrix 3
max_cost := "6"
# The directory for the --json files of one matrix. `just compare` reads two of these.
out := "evals/results/latest"

# List the recipes.
default:
    @just --list

# Run each free check.
check: test lint types validate

# Run the linter tests.
test:
    python3 -m unittest discover -s tests

# Lint the prose of the repo with the skill itself.
lint:
    {{ lint }} --baseline {{ readme_baseline }} README.md
    {{ lint }} --baseline {{ skill_baseline }} {{ skill }}/SKILL.md
    {{ lint }} --baseline {{ rules_baseline }} {{ skill }}/references/writing-rules.md
    {{ lint }} {{ skill }}/references/examples.md evals/SOURCES.md evals/LESSONS.md

# Lint one file or text. Pass a path, or "-" for stdin.
lint-one +args:
    {{ lint }} {{ args }}

# Type check the scripts and the tests. ste-lint has no .py name, so it needs its own path.
types:
    MYPYPATH={{ scripts }} uvx zuban@latest check {{ scripts }} {{ lint }} tests evals/compare-runs.py

# Check the manifests and the layout.
validate:
    claude plugin validate .

# Run the eval cases on one model. This makes paid model runs.
eval model runs="1" ablation="none":
    mkdir -p {{ out }}
    CLAUDE_CODE_EFFORT_LEVEL={{ effort }} claude plugin eval . \
      --model {{ model }} --judge-model {{ judge }} --runs {{ runs }} \
      --ablation {{ ablation }} -j {{ concurrency }} --max-cost-usd {{ max_cost }} \
      --trust-plugin --no-publish --allow-tools "Bash($PWD/{{ lint }} *)" \
      --json {{ out }}/{{ model }}-{{ effort }}.json

# Run the eval cases on each model of the matrix. This makes paid model runs.
eval-matrix runs="1":
    for model in {{ models }}; do just out={{ out }} max_cost={{ max_cost }} eval "$model" {{ runs }}; done

# Compare two eval runs case by case. Pass two directories of --json files.
compare before after:
    evals/compare-runs.py {{ before }} {{ after }}

# Run one eval case on one model, for a fix. This makes paid model runs.
# --keep-temp holds the scaffold, so the tracePath of each run still exists and
# shows every tool call. Without it the harness removes the trace, and the
# evidence field of each llm grader is all that stays.
eval-case model case runs="3":
    mkdir -p {{ out }}
    CLAUDE_CODE_EFFORT_LEVEL={{ effort }} claude plugin eval . \
      --model {{ model }} --judge-model {{ judge }} --runs {{ runs }} --ablation none \
      --case {{ case }} -j {{ concurrency }} --max-cost-usd {{ max_cost }} \
      --trust-plugin --no-publish --keep-temp --allow-tools "Bash($PWD/{{ lint }} *)" \
      --json {{ out }}/{{ case }}-{{ model }}.json

# Measure the trigger rate of the description. This makes paid model runs.
# The weakest model of the matrix misses the most triggers, so it is the default here.
triggers rounds="3" set="validation" model="claude-haiku-5-5":
    evals/trigger-queries.sh {{ rounds }} {{ set }} {{ model }}

# Measure how often the skill fires on the eval prompts. This makes paid model runs.
# One eval pass samples the skill choice once per case, which is too few to judge
# a description, and this samples the choice alone at the effort of the matrix.
fire-rate rounds="3" model="claude-haiku-5-5" case="":
    CLAUDE_CODE_EFFORT_LEVEL={{ effort }} evals/fire-rate.sh {{ rounds }} {{ model }} {{ case }}

# Install the plugin from the marketplace.
install:
    claude plugin marketplace add {{ marketplace }}
    claude plugin install {{ plugin }}@asd-ste100-skill
