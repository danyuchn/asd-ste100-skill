# Linter Edge-Case Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the STE linter so it detects incomplete Markdown list items that end with a coordinating conjunction, and document the linter's structural limits.

**Architecture:** Keep scripts/ste-lint.py deterministic and standard-library-only. Add a context-aware helper that groups supported Markdown list items, checks each item's final meaningful non-code line, and preserves the existing code-fence and inline-code behavior. Add regression coverage to the existing --selftest function. Add one synthetic example that intentionally triggers the new rule.

**Tech Stack:** Python 3 standard library, regular expressions, Markdown, Git worktree.

**Spec:** The approved bounded design in the task conversation: use a privacy-safe synthetic example, detect dangling list conjunctions, add regression tests, document that the linter does not preserve meaning, and keep semantic comparison out of this focused change.

## Global Constraints

- Keep the linter standard-library-only.
- Keep the existing command-line interface, JSON fields, exit-code behavior, and --baseline behavior unchanged.
- Ignore fenced code blocks and inline code, as the linter does for its existing rules.
- Restrict the new rule to supported Markdown list markers at the start of a line. Do not flag ordinary prose that ends with and or or.
- Treat an indented continuation line as part of the preceding list item. Do not flag a list item when its conjunction continues onto an indented line.
- Recognize unordered and ordered list markers with up to three leading ASCII spaces and one or more ASCII spaces after the marker. Do not claim support for blockquote lists in this change.
- Do not flag standalone four-space-indented code or list-like text inside fenced code blocks. Within an active list item, treat text at the computed continuation indentation as item content; do not claim to distinguish code from valid indented Markdown content.
- Mark the new rule advisory-free because an incomplete list item is a hard structural error in STE output.
- Do not copy the Metis design document or private content into the fork.
- Do not add a source-versus-rewrite semantic checker in this change.
- State the distinction between structural linting and meaning preservation in the README.

---

## File Map

- scripts/ste-lint.py — Add the dangling-conjunction rule and regression cases in selftest().
- examples/linter-edge-cases.md — Add a synthetic document with intentional violations and no project-specific information.
- README.md — Document the new rule, its example command, and the linter's semantic and Markdown-scope limits.
- SKILL.md — Keep the skill's linter rule inventory consistent with the implementation.

## Task 1: Confirm the contribution workspace

**Files:**

- No file changes.

**Interfaces:**

- Consumes: The fork at F:/Repositories/Projects/Metis/asd-ste100-skill.
- Produces: An isolated worktree at F:/Repositories/Projects/Metis/asd-ste100-skill-worktree on branch fix/linter-dangling-conjunctions.

- [ ] **Step 1: Confirm the worktree and branch**

Run:

    git -C F:/Repositories/Projects/Metis/asd-ste100-skill worktree list
    git -C F:/Repositories/Projects/Metis/asd-ste100-skill-worktree status --short --branch

Expected: The worktree list contains asd-ste100-skill-worktree on fix/linter-dangling-conjunctions. The status output shows a clean branch after the committed plan is present.

- [ ] **Step 2: Confirm the remotes**

Run:

    git -C F:/Repositories/Projects/Metis/asd-ste100-skill remote -v

Expected: origin points to https://github.com/kidego5150/asd-ste100-skill.git. upstream points to https://github.com/danyuchn/asd-ste100-skill.git.

- [ ] **Step 3: Refresh the remote refs before implementation**

Run:

    git -C F:/Repositories/Projects/Metis/asd-ste100-skill fetch --prune origin
    git -C F:/Repositories/Projects/Metis/asd-ste100-skill fetch --prune upstream master
    git -C F:/Repositories/Projects/Metis/asd-ste100-skill rev-parse master origin/master upstream/master
    git -C F:/Repositories/Projects/Metis/asd-ste100-skill-worktree merge-base --is-ancestor upstream/master HEAD

Expected: The commands create or refresh origin/master and upstream/master, print the three hashes, and return exit code 0 for the ancestor check. If the branch is not based on the refreshed upstream/master, reconcile the feature branch with a normal merge or rebase after inspection. Do not alter or push the default master branch as part of this feature.

## Task 2: Add failing regression cases

**Files:**

- Modify: scripts/ste-lint.py, inside selftest() after the existing code-block checks.

**Interfaces:**

- Consumes: The existing lint(text, filename) function and its finding dictionaries.
- Produces: Failing assertions for the dangling-conjunction rule.

- [ ] **Step 1: Add the failing assertions**

Add this block to selftest():

    # all supported list markers, case variants, and trailing whitespace
    findings, _ = lint(
        "- Confirm the target and\n"
        "* Record the result OR  \n"
        "+ Close the panel\n"
        "1. Start the task and\n"
        "2) Stop the task OR"
    )
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 4, dangling
    assert all(f["level"] == "advisory-free" for f in dangling), dangling

    # valid continuation lines and standalone four-space code are ignored
    findings, _ = lint("  - Confirm the target and\n    record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Confirm the target\n  and")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["line"] == 1, dangling
    findings, _ = lint("    - code and")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("> - Confirm the target and\n> - Record the result or")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Do this and\n~~~\ncode and\n~~~")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["line"] == 1, dangling
    findings, _ = lint("```text\n- code and\n```")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)

    # one- and three-space markers and ordered continuation width
    findings, _ = lint(" - Start the task and\n   record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("-  Start the task and\n   record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("-\tStart the task and")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("   - Start the task and", filename="fixture.md")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["col"] == 4, dangling
    assert dangling[0]["file"] == "fixture.md"
    assert dangling[0]["match"].endswith("and")
    assert "Complete the item" in dangling[0]["message"]
    findings, _ = lint("100. Start the task and\n  unrelated text")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1, dangling
    findings, _ = lint("- Start the task and.\n- Stop the task or,")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Start the task and\n\n  record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Parent item and\n  - Nested item or")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert [f["line"] for f in dangling] == [1, 2], dangling

    # ordinary prose, inline code, and fenced code are ignored
    findings, _ = lint("The process may include steps and")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Use `and` as a label")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("~~~\n- code and\n~~~")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)

- [ ] **Step 2: Run the self-test to verify that it fails**

Run:

    python scripts/ste-lint.py --selftest

Expected: FAIL with an AssertionError because no dangling-conjunction findings exist yet. The failure must come from the new assertions, not from a syntax error.

- [ ] **Step 3: Keep the failing test uncommitted**

Do not commit the failing test. Commit the test and implementation together after the self-test passes in Task 3.

## Task 3: Implement the dangling-conjunction rule

**Files:**

- Modify: scripts/ste-lint.py, near the existing line-based rules and inside lint().

**Interfaces:**

- Consumes: The complete text passed to lint() and the existing filename argument.
- Produces: Finding dictionaries with rule="dangling-conjunction", level="advisory-free", the list-item start line, and a repair message.

- [ ] **Step 1: Add the list-item scanner**

Add these constants near CODE_FENCE and INLINE_CODE:

    LIST_ITEM_START = re.compile(
        r"^(?P<indent> {0,3})(?P<marker>[-*+]|\d+[.)])(?P<gap> +)(?P<body>.*)$"
    )
    CONJUNCTION_END = re.compile(r"\b(?:and|or)\s*$", re.I)

Add these helpers near lint():

    def _leading_spaces(line):
        return len(line) - len(line.lstrip(" "))


    def _is_list_continuation(line, content_indent):
        if not line.strip():
            return True
        if LIST_ITEM_START.match(line):
            return False
        return _leading_spaces(line) >= content_indent


    def _dangling_conjunction_findings(text, filename):
        lines = text.splitlines()
        findings = []
        in_fence = False
        index = 0
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if CODE_FENCE.match(stripped):
                in_fence = not in_fence
                index += 1
                continue
            if in_fence:
                index += 1
                continue
            start = LIST_ITEM_START.match(line)
            if not start:
                index += 1
                continue

            content_indent = (len(start.group("indent"))
                              + len(start.group("marker"))
                              + len(start.group("gap")))
            item_lines = [(index, start.group("body"))]
            next_index = index + 1
            item_fence = False
            while next_index < len(lines):
                candidate = lines[next_index]
                candidate_stripped = candidate.strip()
                if CODE_FENCE.match(candidate_stripped):
                    # Fence delimiters are state markers, not meaningful item lines.
                    item_fence = not item_fence
                    next_index += 1
                    continue
                if item_fence:
                    next_index += 1
                    continue
                if not _is_list_continuation(candidate, content_indent):
                    break
                item_lines.append((next_index, candidate))
                next_index += 1

            meaningful = []
            for line_index, item_line in item_lines:
                cleaned = INLINE_CODE.sub("", item_line).strip()
                if cleaned:
                    meaningful.append((line_index, cleaned))
            if meaningful and CONJUNCTION_END.search(meaningful[-1][1]):
                findings.append({
                    "file": filename,
                    "line": index + 1,
                    "col": start.start("marker") + 1,
                    "rule": "dangling-conjunction",
                    "level": "advisory-free",
                    "match": meaningful[-1][1],
                    "message": "List item ends with a coordinating conjunction. Complete the item or join it with the next item.",
                })
            index = next_index
        return findings

The helper must group all contiguous indented continuation lines before checking the final meaningful line. `content_indent` is the item indentation plus the marker width plus the number of ASCII spaces after the marker, so ordered markers with more than one digit and multiple post-marker spaces use the correct continuation threshold. Any supported list marker ends the current item, regardless of indentation; the scanner evaluates that marker as a separate candidate. This avoids attributing a nested candidate to its parent without pretending to parse nested-list semantics. Blank lines remain part of the scan but do not become the final meaningful line. Fenced-code delimiters and fenced-code lines are skipped and never become meaningful item lines. The helper must not flag ordinary prose, inline-code content, standalone four-space-indented code, or fenced-code content. It intentionally does not parse blockquote list syntax, lazy continuation, or full nested-list semantics in this change. A tab after a marker is outside the supported grammar.

- [ ] **Step 2: Wire the helper into lint()**

Call `_dangling_conjunction_findings(text, filename)` exactly once from `lint()` and extend the existing `findings` list before the final sort. Do not add the rule to `RULES`, because its result depends on multi-line list context rather than one line and one regular expression.

- [ ] **Step 3: Run the self-test after implementation**

Run:

    python scripts/ste-lint.py --selftest

Expected: selftest OK and exit code 0. The assertions cover all supported marker forms, zero-to-three leading spaces, multiple post-marker spaces, case, trailing whitespace, final-line continuation behavior, ordered-marker width, blank lines, nested-marker boundaries, adjacent and fenced code, standalone indented code, inline code, punctuation, finding fields, and unsupported blockquote syntax.

- [ ] **Step 4: Commit the test and implementation together**

Run:

    git add scripts/ste-lint.py
    git commit -m "fix: flag dangling conjunctions in lists"

Expected: The commit contains both the new self-test assertions and the implementation. Do not leave a deliberately failing test in a commit.

## Task 4: Add the synthetic edge-case example

**Files:**

- Create: examples/linter-edge-cases.md.

**Interfaces:**

- Consumes: The new dangling-conjunction rule.
- Produces: A privacy-safe fixture with two intentional hard findings and one ignored fenced-code case.

- [ ] **Step 1: Create the example document**

Create examples/linter-edge-cases.md with this exact content:

    # Linter Edge Cases

    This file has intentional structural violations. Use it to test the linter.

    ## Incomplete list items

    - Set the target and
    - Record the result or

    ## Fenced code

    ~~~text
    - This line ends with and
    ~~~

- [ ] **Step 2: Run the example through the linter**

Run:

    python scripts/ste-lint.py examples/linter-edge-cases.md

Expected: The linter reports exactly two dangling-conjunction findings on the two list items. It reports no finding for the fenced-code line. The command exits with code 1 because the default hard-violation baseline is 0.

- [ ] **Step 3: Verify the documented baseline behavior**

Run:

    python scripts/ste-lint.py --baseline 2 examples/linter-edge-cases.md

Expected: The command reports the same two findings and exits with code 0.

- [ ] **Step 4: Commit the example**

Run:

    git add examples/linter-edge-cases.md
    git commit -m "test: add linter edge-case example"

## Task 5: Document scope and limitations

**Files:**

- Modify: README.md, at the existing sentence beginning "The structural rules it checks are mechanical" and in the linter rule list.
- Modify: SKILL.md, in the Process and Additional Resources linter descriptions.

**Interfaces:**

- Consumes: The linter's actual rule set and the new example path.
- Produces: User-facing instructions that explain how to run the example and what the linter cannot verify.

- [ ] **Step 1: Add the linter limitation text to README.md**

Add this paragraph after the existing sentence beginning "The structural rules it checks are mechanical":

    The linter checks structural patterns only. It does not compare an original text with a rewrite, verify that requirement strength stayed the same, or prove that the rewrite preserved meaning. A zero-violation result means that the configured structural checks found no problems.

Add this paragraph after the structural-lint limitation text:

    The dangling-conjunction rule checks list markers at the start of a line with zero to three leading spaces and ASCII spaces after the marker. It checks indented continuation lines up to the final meaningful line. It does not parse list syntax inside blockquotes, lazy continuation, or full nested-list semantics. A standalone line with four or more leading spaces is not treated as a list marker. Within an active list item, indentation at the computed content column is treated as continuation text. Fence detection follows the linter's existing simple rule: a stripped line beginning with three backticks or three tildes toggles the fence state.

- [ ] **Step 2: Keep the skill rule inventory current**

Update the linter rule list in `SKILL.md` to include dangling-conjunction wherever the existing linter checks are enumerated, including the Process step and Additional Resources entry. Do not claim that the rule checks semantic preservation.

- [ ] **Step 3: Add the edge-case example command**

Add this paragraph after the Markdown-scope paragraph:

    The intentionally invalid examples/linter-edge-cases.md file demonstrates incomplete Markdown list items. Run python scripts/ste-lint.py examples/linter-edge-cases.md to confirm that the linter reports the two expected findings. The file is a test fixture and should not be used as compliant STE prose.

Add `dangling-conjunction` to README.md item 3, which lists the rules that the linter flags.

- [ ] **Step 4: Review the documentation for accuracy**

Run:

    rg -n "linter checks structural|linter-edge-cases|preserved meaning|dangling-conjunction|blockquote|nested-list" README.md SKILL.md

Expected: README.md contains the structural and Markdown-scope limitations, the example path, the command, and the new rule in its linter list. SKILL.md lists dangling-conjunction with the other linter checks. Neither file claims that the linter verifies semantic preservation.

- [ ] **Step 5: Commit the documentation**

Run:

    git add README.md SKILL.md
    git commit -m "docs: clarify linter scope"

## Task 6: Run the complete verification set

**Files:**

- No additional file changes.

**Interfaces:**

- Consumes: The complete branch state.
- Produces: Evidence that the regression tests, fixture behavior, syntax, and working tree are correct.

- [ ] **Step 1: Run the built-in self-test**

Run:

    python scripts/ste-lint.py --selftest

Expected: selftest OK and exit code 0.

- [ ] **Step 2: Run the intentional-failure fixture**

Run:

    python scripts/ste-lint.py --json examples/linter-edge-cases.md

Expected: Valid JSON with exactly two findings, both named dangling-conjunction, both marked advisory-free, hard_count equal to 2, and exit code 1.

- [ ] **Step 3: Run the fixture with its allowed baseline**

Run:

    python scripts/ste-lint.py --baseline 2 examples/linter-edge-cases.md

Expected: The same two findings and exit code 0.

- [ ] **Step 4: Check Python syntax without generating artifacts**

Run:

    python -c "import ast, pathlib; ast.parse(pathlib.Path('scripts/ste-lint.py').read_text(encoding='utf-8')); print('syntax OK')"

Expected: `syntax OK` and exit code 0. No `__pycache__` directory is created.

- [ ] **Step 5: Check whitespace and the final diff**

Run:

    git diff --check upstream/master...HEAD
    git status --short --branch
    git log --oneline -5

Expected: git diff --check produces no output for the committed branch diff. The branch contains the two committed plan revisions plus the three focused implementation commits and no unrelated files. The working tree is clean.

- [ ] **Step 6: Prepare the upstream review information**

Run:

    git fetch --prune upstream master
    git diff upstream/master...HEAD --stat
    git diff upstream/master...HEAD -- scripts/ste-lint.py README.md SKILL.md examples/linter-edge-cases.md

Expected: The diff contains the committed plan, the new linter rule, its regression coverage, the synthetic example, and the README and SKILL.md scope notes. No Metis design content appears. The upstream ref was refreshed before the comparison.

Suggested pull request title:

    Detect dangling conjunctions in Markdown list items

Suggested pull request summary:

    The linter previously accepted Markdown list items that ended with and or or. This change adds a deterministic structural rule, regression coverage, and a privacy-safe example. The README now states that the linter checks structure and cannot verify semantic preservation.

## Out of Scope

This change does not add a semantic source-versus-rewrite comparator. It does not attempt to detect weakened modality, changed requirement strength, unsupported actors, or other meaning changes. Those checks require a separate design and review process.
