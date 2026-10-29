#!/usr/bin/env python3
"""Compare two eval runs of the same suite, case by case.

Usage: evals/compare-runs.py BEFORE_DIR AFTER_DIR
Each directory holds the `--json` files that `just eval` writes, one for each model.
It prints one table for each model, then the suite totals. It reads files only.
It compares the `with` arm, which holds the runs that had the plugin.
"""
import json
import pathlib
import sys


def load(d: pathlib.Path) -> dict[str, dict]:
    """Map a model name to its run, from the JSON files of one directory."""
    runs = {}
    for f in sorted(d.glob("*.json")):
        name = f.name.replace("-medium.json", "").replace("claude-", "")
        runs[name] = json.loads(f.read_text())
    return runs


def grader_fails(case: dict) -> set[str]:
    """The names of the graders that failed in the plugin arm of one case."""
    out = set()
    for run in case["arms"].get("with", []):
        for g in run["graders"]:
            if not g["passed"]:
                out.add(g["name"])
    return out


def aborted(case: dict) -> int:
    """The runs that ended on an error, such as the turn limit of the case.

    Such a run scores every grader against an empty reply, so it reads as a
    quality collapse. The caller prints it apart.
    """
    return sum(1 for run in case["arms"].get("with", []) if run.get("error"))


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    before, after = (pathlib.Path(a) for a in sys.argv[1:3])
    runs_b, runs_a = load(before), load(after)
    models = [m for m in runs_a if m in runs_b]
    if not models:
        print("no model appears in both directories", file=sys.stderr)
        return 2
    for m in sorted(set(runs_b) ^ set(runs_a)):
        where = before if m in runs_b else after
        print(f"!! {m} appears in {where} only, so it is left out", file=sys.stderr)

    for model in models:
        rb, ra = runs_b[model], runs_a[model]
        cases_b = {c["name"]: c for c in rb["cases"]}
        names_a = {c["name"] for c in ra["cases"]}
        print(f"######## {model}")
        for name in sorted(n for n in cases_b if n not in names_a):
            print(f"  {name:<30} GONE     score {cases_b[name]['aggregates']['score']:.2f}")
        for case in ra["cases"]:
            name = case["name"]
            old = cases_b.get(name)
            if old is None:
                print(f"  {name:<30} NEW      score {case['aggregates']['score']:.2f}")
                continue
            sb = old["aggregates"]["score"]
            sa = case["aggregates"]["score"]
            pb = old["aggregates"]["passRate"] == 1.0
            pa = case["aggregates"]["passRate"] == 1.0
            if pb == pa and abs(sa - sb) < 0.005:
                mark = "same"
            elif pa and not pb:
                mark = "FIXED"
            elif pb and not pa:
                mark = "BROKE"
            else:
                mark = "moved"
            still = sorted(grader_fails(case))
            tail = ("  fails: " + ", ".join(still)) if still else ""
            n_bad = aborted(case)
            if n_bad:
                tail = f"  [{n_bad} run(s) ended on an error]" + tail
            print(f"  {name:<30} {mark:<5} {sb:.2f} -> {sa:.2f}{tail}")
        ab, aa = rb["aggregates"], ra["aggregates"]
        print(
            f"  TOTAL cases {ab['casesPassed']}/{ab['casesTotal']}"
            f" -> {aa['casesPassed']}/{aa['casesTotal']}"
            f" | score {ab['overallScore']:.3f} -> {aa['overallScore']:.3f}"
            f" | cost ${rb['costUsd']:.2f} -> ${ra['costUsd']:.2f}"
        )
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
