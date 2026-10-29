#!/usr/bin/env bash
# Prints one JSON line per query in trigger-queries.json: how often the ste-rewrite skill triggered.
# Usage: evals/trigger-queries.sh [runs] [train|validation] [model]
# Each query and run is one paid `claude -p` call. Needs claude and jq.
# --setting-sources project keeps user plugins, skills, and CLAUDE.md out of the test.
# The model decides the trigger rate, so pass the weakest model of the matrix.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
runs=${1:-3}
split=${2:-}
model=${3:-}
model_flag=()
[ -n "$model" ] && model_flag=(--model "$model")
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
fired='any(.[]; .type == "assistant" and any(.message.content[]?;
	.type == "tool_use" and .name == "Skill" and (.input.skill | test("(^|:)ste-rewrite$"))))'
jq -c --arg split "$split" '.[] | select($split == "" or .split == $split)' "$root/evals/trigger-queries.json" |
	while read -r item; do
		hits=0
		for _ in $(seq "$runs"); do
			out=$(claude -p "$(jq -r .query <<<"$item")" --plugin-dir "$root" --setting-sources project --allowedTools Skill \
				"${model_flag[@]}" --output-format stream-json --verbose </dev/null)
			# A failed run must stop the script, or every should-not-trigger query passes.
			jq -e -s 'any(.[]; .type == "result")' >/dev/null <<<"$out" || { echo "claude gave no result" >&2; exit 1; }
			if jq -e -s "$fired" >/dev/null <<<"$out"; then
				hits=$((hits + 1))
			fi
		done
		jq -nc --argjson item "$item" --argjson hits "$hits" --argjson runs "$runs" \
			'($hits / $runs) as $rate | $item + {triggers: $hits, runs: $runs, rate: $rate,
			pass: (if $item.should_trigger then $rate > 0.5 else $rate < 0.5 end)}'
	done
