#!/usr/bin/env bash
# Prints one line per eval case: how often the ste-rewrite skill fired on its prompt.
# Usage: evals/fire-rate.sh [runs] [model] [case]
# Each prompt and run is one paid `claude -p` call. Needs claude and jq.
# A `claude plugin eval` pass gives one sample of the skill choice per case and
# pays a judge for each grader. This script samples the choice alone, so a
# description change gets more samples for a small part of the price.
# --setting-sources project keeps user plugins, skills, and CLAUDE.md out of the test.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
runs=${1:-3}
model=${2:-}
only=${3:-}
model_flag=()
[ -n "$model" ] && model_flag=(--model "$model")
# The skill reads a file and runs the linter, so the eval cases allow these tools.
tools="Skill,Read,Bash"
trigger_tag="trigger"
fired='any(.[]; .type == "assistant" and any(.message.content[]?;
	.type == "tool_use" and .name == "Skill" and (.input.skill | test("(^|:)ste-rewrite$"))))'
body_of='
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text()
head, _, body = text.partition("---\n")[2].partition("---\n")
print(body.strip() if body else text.strip())
print("want=no" if sys.argv[2] in head else "want=yes")
'
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
for dir in "$root"/evals/*/; do
	name=$(basename "$dir")
	[ -f "$dir/prompt.md" ] || continue
	[ -n "$only" ] && [ "$only" != "$name" ] && continue
	parsed=$(python3 -I -c "$body_of" "$dir/prompt.md" "$trigger_tag")
	want=${parsed##*$'\n'}
	prompt=${parsed%$'\n'*}
	hits=0
	for _ in $(seq "$runs"); do
		out=$(claude -p "$prompt" --plugin-dir "$root" --setting-sources project --allowedTools "$tools" \
			"${model_flag[@]}" --output-format stream-json --verbose </dev/null)
		# A failed run must stop the script, or a case with no result reads as no trigger.
		jq -e -s 'any(.[]; .type == "result")' >/dev/null <<<"$out" || { echo "claude gave no result" >&2; exit 1; }
		if jq -e -s "$fired" >/dev/null <<<"$out"; then
			hits=$((hits + 1))
		fi
	done
	printf '%-28s %s %d/%d\n' "$name" "$want" "$hits" "$runs"
done
