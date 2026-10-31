"""Built-in tests for the STE linter, run by --selftest."""
import contextlib
import io
import json
import os
import tempfile

from ste_lint import lint


def selftest():
    from ste_cli import _rule_list, main
    bad = ("The panel is removed; spin up the job. "
           "Perform an analysis of the seamless log. "
           "We have received the report.")
    findings, _ = lint(bad)
    rules = {f["rule"] for f in findings}
    for expected in ("semicolon", "phrasal-verb", "nominalization",
                     "marketing-adjective", "passive-voice", "present-perfect"):
        assert expected in rules, expected
    # hedges must never be flagged, including modal + perfect infinitive
    findings, _ = lint("The request may have failed. It could be a timeout. "
                       "The disk might have filled.")
    assert findings == [], findings
    # irregular participles: "has run" is a compound tense as much as "has failed"
    findings, _ = lint("The task has run. The job has set the flag. We have begun.")
    assert sum(1 for f in findings if f["rule"] == "present-perfect") == 3, findings
    findings, _ = lint("The job may have run.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    # Modal perfects remain protected across negation and variable whitespace.
    for modal in ("may", "might", "could", "should", "would", "must"):
        for gap in (" ", "  ", "\t", " not "):
            findings, _ = lint(f"The task {modal}{gap}have run.")
            assert not any(f["rule"] == "present-perfect" for f in findings), findings
    findings, _ = lint("The task couldn't have run. The task MAY NOT HAVE RUN.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    findings, _ = lint("It might already have finished. It could not possibly have run. "
                       "It may never have started. It should probably have stopped.")
    assert not any(f["rule"] == "present-perfect" for f in findings), findings
    # an adverb without a modal is not a hedge
    findings, _ = lint("The task already has run. They probably have finished.")
    assert sum(f["rule"] == "present-perfect" for f in findings) == 2, findings
    findings, _ = lint("The task has run. We have begun. The flag is set.")
    assert sum(f["rule"] == "present-perfect" for f in findings) == 2, findings
    assert any(f["rule"] == "passive-voice" for f in findings), findings
    findings, _ = lint("The task is gone.")
    assert not any(f["rule"] == "passive-voice" for f in findings), findings
    # code blocks skipped
    findings, _ = lint("```\nx = a; y = b\n```")
    assert findings == []
    # a fence closes only on the same character, at least as long, with nothing after it
    for text in ("````md\n```\n````\n\nProse; here.",
                 "```\n~~~\n```\n\nProse; here.",
                 "~~~~\n~~~\n~~~~\n\nProse; here."):
        findings, _ = lint(text)
        assert [f["rule"] for f in findings] == ["semicolon"], (text, findings)
    findings, _ = lint("```\n```sh\nx = a; y = b\n```")
    assert findings == [], findings
    # a fence inside a blockquote is a fence
    findings, _ = lint("Text.\n\n> ```\n> x = a; y = b\n> ```\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 7)], findings
    # the dangling-conjunction rule uses the same fence state
    findings, _ = lint("````md\n```\n- Do this and\n````")
    assert findings == [], findings
    findings, _ = lint("- Do this\n  ````md\n  ```\n  code and\n  ````\n- Do that")
    assert findings == [], findings
    # a quoted fence ends with its quote, and a deeper ">" in a fence is code
    for text, lines in (("> ```\n> code\n\nProse; here.", [4]),
                        ("```\n> ```\nx; y\n```\n\nProse; here.", [6]),
                        (">  > ```\n>  > x; y\n>  > ```\n\nProse; here.", [5]),
                        ("> ```\n>     ```\n> x; y\n> ```\n\nProse; here.", [6]),
                        ("```foo`bar\nProse; here.", [2]),
                        ("```\nx; y\n```` \t\n\nProse; here.", [5])):
        findings, _ = lint(text)
        assert [f["line"] for f in findings if f["rule"] == "semicolon"] == lines, (text, findings)
    # the end of a quoted fence in a list item does not join the next line to the item
    findings, _ = lint("- Item\n  > ```\n  > code\nProse and")
    assert findings == [], findings
    # a tab is indent up to the next tab stop of 4, from its real column, also after ">"
    for text, line in (("\t```\n\tx = 1\n\t```\n\nProse; here.", 5),
                       ("```\nx\n\t```\ny; z\n```\n\nProse; here.", 7),
                       ("> ```\n> x\n>\t```\n> Use a; b.", 4),
                       ("> ```\n> x\n>  \t```\n> Use a; b.", 4),
                       (">\t> ```\n>\t> x; y\n>\t> ```\n\nProse; here.", 5),
                       ("- Item\n  ```\n\t```\n\nProse; here.", 5)):
        findings, _ = lint(text)
        assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", line)], (text, findings)
    # a tab-indented fence stays in its list item
    findings, _ = lint("- Run the build and\n\t```\n\tmake\n\t```\n  check the log.")
    assert findings == [], findings
    # a ">" line in an HTML block is text, not a quoted fence. A blank line ends a
    # block that starts with a tag, and a quoted fence after it is a fence.
    for text, lines in (("<div>\n> ```\n> Prose; here.\n> ```\n</div>", [3]),
                        ("<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [3]),
                        ("<!--\n> ```\n> Prose; here.\n> ```\n-->", [3]),
                        ("<div>\n\n> ```\n> x; y\n> ```\n\nProse; here.", [7]),
                        ("<details>\n\n> ```\n> a; b\n> ```\n\n</details>\n\nProse; here.", [9]),
                        ("<pre>\n> ```\n> Prose; here.\n> ```\n</pre>", [3]),
                        ("<?php\n> ```\n> Prose; here.\n> ```\n?>", [3]),
                        ("<![CDATA[\n> ```\n> Prose; here.\n> ```\n]]>", [3]),
                        # inline HTML is no HTML block: the quoted fence after it is a fence
                        ("<span>Label</span>\n> ```\n> a; b\n> ```", []),
                        ("<kbd>Enter</kbd> starts the job.\n> ```\n> a; b\n> ```", []),
                        ("Text.\n<custom>\n> ```\n> a; b\n> ```", []),
                        # a type 7 tag after a heading or a fence starts a block
                        ("# Title\n<custom>\n> ```\n> Prose; here.\n> ```\n</custom>", [4]),
                        ("```\nx\n```\n<img src=\"a.png\">\n> ```\n> Prose; here.\n> ```", [6]),
                        # attribute values may hold "<" and ">", an invalid attribute is no tag
                        ('<span title="a > b">\n> ```\n> Prose; here.\n> ```', [3]),
                        ("<custom a=>\n> ```\n> a; b\n> ```", []),
                        ("<DIV class=x>text\n> ```\n> Prose; here.\n> ```", [3])):
        findings, _ = lint(text)
        assert [f["line"] for f in findings if f["rule"] == "semicolon"] == lines, (text, findings)
    # a fence at column 0 ends a list item
    findings, _ = lint("- Do this and\n```\nx\n```\n  done")
    assert [(f["rule"], f["line"]) for f in findings] == [("dangling-conjunction", 1)], findings
    # a quoted fence also ends on a line with fewer quote levels that is not blank
    for text, line in (("> ```\n> x\nProse; here.", 3), ("> > ```\n> x; y", 2)):
        findings, _ = lint(text)
        assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", line)], (text, findings)
    # a closing fence up to three columns deeper than the opening fence closes it
    findings, _ = lint("```\nx; y\n   ```\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 5)], findings
    # a tilde fence opens with a backtick in its info string
    findings, _ = lint("~~~ a`b\nx; y\n~~~\n\nProse; here.")
    assert [(f["rule"], f["line"]) for f in findings] == [("semicolon", 5)], findings
    # an alert marker after a fence in the same quote is text, as GitHub shows it
    body = " ".join(["word"] * 25) + "."
    findings, _ = lint(f"> ```\n> x\n> ```\n> [!NOTE]\n> {body}")
    assert [f["rule"] for f in findings] == ["long-sentence"], findings
    # a quoted fence after a list item does not join the item
    findings, _ = lint("- Do this and\n\n> ```\n> code\n> ```\n  done")
    assert [f["rule"] for f in findings] == ["dangling-conjunction"], findings
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
    assert [f["line"] for f in dangling] == [1, 2, 4, 5], dangling
    assert [f["col"] for f in dangling] == [1, 1, 1, 1], dangling
    assert all(f["level"] == "advisory-free" for f in dangling), dangling

    # valid continuation lines and standalone four-space code are ignored
    findings, _ = lint("  - Confirm the target and\n    record the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint("- Confirm the target and\n\trecord the result.")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings), findings
    findings, _ = lint("- Confirm the target\n  and")
    dangling = [f for f in findings if f["rule"] == "dangling-conjunction"]
    assert len(dangling) == 1 and dangling[0]["line"] == 2, dangling
    assert dangling[0]["col"] == 3, dangling
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
    findings, _ = lint("- Combine `left` and `right`")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings), findings
    findings, _ = lint("~~~\n- code and\n~~~")
    assert not any(f["rule"] == "dangling-conjunction" for f in findings)
    findings, _ = lint(("word " * 30).strip() + ".")
    assert any(f["rule"] == "long-sentence" for f in findings)
    # Markdown table syntax is layout, not prose. Each cell stays lintable.
    short_cell = " ".join(f"term{number}" for number in range(1, 25)) + "."
    for table in (
            "| Label | Detail |\n"
            "| --- | --- |\n"
            f"| Clear | {short_cell} |",
            "Label | Detail\n"
            "--- | ---\n"
            f"Clear | {short_cell}"):
        findings, words_total = lint(table)
        assert not any(f["rule"] == "long-sentence" for f in findings), findings
        assert words_total == 27, words_total
    # GFM also accepts one-dash separators, one column, and ragged body rows.
    short_row = " ".join(f"term{number}" for number in range(1, 9))
    for table in (
            "| Label | Detail |\n|-|-|\n" + f"| {short_row} | {short_row} |\n" * 5,
            "| Label |\n| --- |\n" + f"| {short_row} |\n" * 8,
            "| Label | Detail |\n| --- | --- |\n| x |\n"
            + f"| {short_row} | {short_row} | extra |\n" * 2):
        findings, _ = lint(table)
        assert not any(f["rule"] == "long-sentence" for f in findings), (table, findings)
    long_cell = " ".join(f"term{number}" for number in range(1, 27)) + "."
    findings, _ = lint(
        "| Label | Detail |\n"
        "| --- | --- |\n"
        f"| Clear | {long_cell} |"
    )
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert len(long_sentences) == 1, long_sentences
    assert long_sentences[0]["match"] == "26 words", long_sentences
    # synonym rotation: second member flagged, first named as the keeper
    findings, _ = lint("Check the config file. Then verify the output. Verify twice.")
    rot = [f for f in findings if f["rule"] == "synonym-rotation"]
    assert len(rot) == 1 and "'verify' and 'check'" in rot[0]["message"], rot
    # single consistent term: no flag
    findings, _ = lint("Check the config. Check the output.")
    assert not any(f["rule"] == "synonym-rotation" for f in findings)
    # character references and link targets are markup, not prose
    findings, _ = lint("Press Ctrl&nbsp;C to stop &#59; &#x3B; &rarr; now. "
                       "See [the docs](https://x.io/a;b) or <https://x.io/a;b>.")
    assert not any(f["rule"] == "semicolon" for f in findings), findings
    findings, _ = lint("Press [stop](https://x.io); then wait. Use & ; here.")
    assert [f["col"] for f in findings if f["rule"] == "semicolon"] == [27, 46], findings
    # per-file labels
    findings, _ = lint("a; b", filename="x.md")
    assert findings[0]["file"] == "x.md"
    # inline code is masked, not deleted, so columns match the source
    findings, _ = lint("Run `make all` then spin up the node.")
    phrasal = [f for f in findings if f["rule"] == "phrasal-verb"]
    assert len(phrasal) == 1 and phrasal[0]["col"] == 21, phrasal
    # a sentence ends after closing quotes and brackets
    twenty = " ".join(["word"] * 20)
    findings, _ = lint(f'He asked "{twenty}?" Then {twenty} ended. (It {twenty}.) Next.')
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # abbreviations do not end a sentence
    findings, _ = lint(f"Use a tool, e.g. the {twenty} linter here now.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"Compare A vs. B in the {twenty} test.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # a sentence wrapped across lines is counted once, at its start
    findings, _ = lint(f"Intro text here.\nThe {twenty}\nwrapped tail words go here.")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert len(long_sentences) == 1, long_sentences
    assert (long_sentences[0]["line"], long_sentences[0]["col"]) == (2, 1), long_sentences
    findings, _ = lint(f"- Item {twenty}\n  continued in the same item.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # leading front matter is skipped; line numbers after it stay true
    findings, words_total = lint(f"---\nname: x\ndescription: {twenty} {twenty}.\n"
                                 "tags:\n  - a and\n---\nThe job is robust.")
    assert [(f["line"], f["rule"]) for f in findings] == [(7, "marketing-adjective")], findings
    assert words_total == 4, words_total
    # a later --- pair is a thematic break, not front matter
    findings, _ = lint(f"Intro.\n\n---\n{twenty} {twenty}.\n---")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # blank lines, headings, rules, list items, and quotes end a prose block
    for sep in ("\n\n", "\n# Heading\n", "\n---\n", "\n- ", "\n> "):
        findings, _ = lint(f"First {twenty} line{sep}Second {twenty} line.")
        assert not any(f["rule"] == "long-sentence" for f in findings), (sep, findings)
    # a GitHub alert marker on the first line of a quote is not a word of the body
    body = " ".join(["word"] * 25) + "."
    for alert in ("> [!NOTE]", "> [!tip]", ">[!Warning]", ">  [!CAUTION]  "):
        findings, _ = lint(f"{alert}\n> {body}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (alert, findings)
    for text in (f"Text.\n\n> [!NOTE]\n> {body}", f"> Text.\n~~~\ncode\n~~~\n> [!NOTE]\n> {body}"):
        findings, _ = lint(text)
        assert not any(f["rule"] == "long-sentence" for f in findings), (text, findings)
    # Inside HTML containers the marker is text: marker plus body is 26 words.
    for opening, closing in (("<details>", "</details>"),
                             ('<DIV class="note">', "</DIV>"),
                             ("<section><details>", "</details></section>")):
        findings, _ = lint(f"{opening}\n\n> [!NOTE]\n> {body}\n\n{closing}")
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (opening, findings)
        findings, _ = lint(f"{opening}\n{closing}\n\n> [!NOTE]\n> {body}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (opening, findings)
    findings, _ = lint(f"> [!NOTE]\n> {body}")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # An inner close or a fenced closing tag must not close the outer container.
    for content in ("<details>\n<div>\n</div>",
                    "<details>\n~~~\n</details>\n~~~"):
        findings, _ = lint(f"{content}\n\n> [!NOTE]\n> {body}\n\n</details>")
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (content, findings)
    # Fenced, commented, inline, void, and self-closing tags do not open containers.
    for content in ("```html\n<details>\n```", "<!-- <details> -->",
                    "<span>Text.</span>", "<hr>", "<div />",
                    "<details></details>", "</details>"):
        findings, _ = lint(f"{content}\n\n> [!NOTE]\n> {body}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (content, findings)
    # GitHub shows these markers as text, so they stay words. GitHub shows the
    # last two as alerts, but no blank line or fence proves that a quote starts.
    for text in (f"> [!FOO]\n> {body}", f"> [!NOTE] {body}", f"> Intro.\n> [!NOTE]\n> {body}",
                 f"> > [!NOTE]\n> > {body}", f"> Intro.\ncontinuation.\n> [!NOTE]\n> {body}",
                 f"- Item.\n\n  > [!NOTE]\n  > {body}",
                 f"Text.\n> [!NOTE]\n> {body}", f"   > [!NOTE]\n   > {body}"):
        findings, _ = lint(text)
        long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
        assert [f["match"] for f in long_sentences] == ["26 words"], (text, long_sentences)
    # a bold or italic lead sentence ends at its closing emphasis marker
    findings, _ = lint(f"**Lead.** The {twenty} more words here now.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"_Note._ The {twenty} more words here now.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"See **e.g.** the {twenty} linter here now.")
    assert any(f["rule"] == "long-sentence" for f in findings), findings
    # a dotted abbreviation ends a sentence before a capitalized word
    findings, _ = lint(f"The team shipped it in the U.S. Then {twenty} today.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # nested list items, quoted list items, and HTML lines end a prose block
    for text in (f"- First item\n    - First {twenty} line\n      - Second {twenty} line",
                 f"> - First {twenty} line\n> - Second {twenty} line",
                 f"<!-- First {twenty} line -->\nSecond {twenty} line.",
                 f"> First {twenty} line.\n>\n> Second {twenty} line."):
        findings, _ = lint(text)
        assert not any(f["rule"] == "long-sentence" for f in findings), (text, findings)
    # a blockquote prefix is not a word in a wrapped quoted sentence
    findings, _ = lint("> " + "\n> ".join(["word word word word word"] * 5) + ".")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    # a list marker is not a word either, in every marker style
    twenty_five = " ".join(f"term{number}" for number in range(1, 26)) + "."
    for marker in ("-", "*", "+", "1.", "1)", "  -", "> -"):
        findings, _ = lint(f"{marker} {twenty_five}")
        assert not any(f["rule"] == "long-sentence" for f in findings), (marker, findings)
    findings, _ = lint(f"- term0 {twenty_five}")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert [(f["match"], f["col"]) for f in long_sentences] == [("26 words", 3)], long_sentences
    # a code span at the line start does not turn the next token into a list marker
    findings, _ = lint(f"`label` 1) {twenty_five}")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert [f["match"] for f in long_sentences] == ["26 words"], long_sentences
    # bare punctuation is not a word: code-span separators and spaced dashes
    for separator in (", ", " ", " / "):
        names = separator.join(f"`a{number}`" for number in range(30))
        findings, _ = lint(f"The adapters are {names}.")
        assert not any(f["rule"] == "long-sentence" for f in findings), (separator, findings)
    findings, _ = lint(" ".join(f"term{number}" for number in range(1, 25)) + " — term25.")
    assert not any(f["rule"] == "long-sentence" for f in findings), findings
    findings, _ = lint(f"Use `make` — {twenty_five}")
    long_sentences = [f for f in findings if f["rule"] == "long-sentence"]
    assert [f["match"] for f in long_sentences] == ["26 words"], long_sentences
    # a long block stays linear: one short sentence per line, no blank lines
    findings, _ = lint("The agent read the log.\n" * 20000)
    assert not any(f["rule"] == "long-sentence" for f in findings)
    # flags may appear between file paths
    with tempfile.TemporaryDirectory() as tmp:
        paths = [os.path.join(tmp, name) for name in ("a.md", "b.md")]
        for path in paths:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("Short line here.\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert main([paths[0], "--json", paths[1]]) == 0
        assert json.loads(out.getvalue())["words"] == 6, out.getvalue()
        # repeated --disable flags add up instead of replacing each other
        with open(paths[0], "w", encoding="utf-8") as fh:
            fh.write("a; b. " + " ".join(["word"] * 30) + ".\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert main([paths[0], "--json", "--disable", "semicolon",
                         "--disable", "long-sentence"]) == 0
        assert json.loads(out.getvalue())["count"] == 0, out.getvalue()
    # command-line parsing rejects typos and bad values
    for bad in (["--basline", "3"], ["--baseline"], ["--baseline", "x"],
                ["--baseline", "-1"], ["--disable", "passive"], ["--base", "3"]):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                main(bad)
        except SystemExit as e:
            assert e.code == 2, (bad, e.code)
        else:
            raise AssertionError(bad)
    assert _rule_list("passive-voice,present-perfect") == {"passive-voice", "present-perfect"}
    print("selftest OK")
