---
type: regex
pattern: ';[^`\n]*$'
flags: 'm'
match: not_contains
---

The source holds two semicolons: one in the prose, and one inside the code span `cd /tmp && ls; echo done`. The prose one must become a period, and the one in the command must survive, so a count of the semicolons cannot decide this case: a correct reply quotes the command again in a `Kept as-is:` line. This pattern finds a semicolon that reaches the end of its line with no backtick after it, which is a semicolon in prose. It does not catch a prose semicolon on a line that holds a later code span.
