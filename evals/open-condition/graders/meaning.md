---
type: llm
weight: 2
---

The response is a rewrite of this source: "The job may have been cancelled; retry if needed."

Pass only if all of these are true:

1. The cancellation stays possible, not a fact. The rewrite uses "may", "might", or "could" for it.
2. The retry instruction keeps a condition as open as "if needed", such as "if needed" or "if necessary". It fails if the rewrite narrows the condition to a cause that the source does not state, such as "if the job was cancelled".
3. The text has no semicolon.
4. The response is the rewritten text alone. Last lines that start with "Kept as-is:" are allowed. A note that explains how the source was read fails.
