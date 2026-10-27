---
type: llm
weight: 2
---

The response is a rewrite of this source: "The upload might have been rejected because the file could possibly exceed the size limit that has been configured for this workspace, or the token may have expired; try again later."

Pass only if all of these are true:

1. The rewrite states the rejection as possible, not as a fact. It uses "may", "might", or "could" for it.
2. Both causes stay possible, not certain: the file size over the workspace limit, and an expired token. Both causes are present.
3. The limit still belongs to the workspace, and the instruction to try again later is present.
4. The rewrite adds no cause, number, frequency, or step that the source does not state.
5. Each sentence has 25 words or fewer, and the text has no semicolon.
6. The response is the rewritten text alone. Last lines that start with "Kept as-is:" are allowed. A preamble, a list of changes, a rule table, or an offer to explain fails.
