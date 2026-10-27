---
type: llm
weight: 2
---

The source sentence is: "The config file should be checked by the operator before the service is spun up; otherwise the defaults will be used."

Pass only if all of these are true:

1. The response has a Markdown table with a column for the rule, the original text, and the rewrite.
2. The table names at least the semicolon and the phrasal verb "spun up", and the response names or fixes the passive voice ("should be checked by the operator", "will be used"), as a violation or as an advisory finding.
3. The rewrite keeps "should" as a recommendation or turns it into an instruction to the operator, and keeps the fallback to the defaults when the operator does not check the file.
4. The rewrite has no semicolon and no phrasal verb, and names the operator as the actor.
5. The response does not say that the result complies with ASD-STE100.
