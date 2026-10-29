---
type: llm
weight: 2
---

Source: "The job may have been cancelled; retry if needed."

Pass only if the retry instruction keeps a condition as open as "if needed", such as "if needed" or "if necessary". A rewrite that narrows the condition to a cause that the source does not state, such as "if the job was cancelled", fails.
"If needed" and "if necessary" are not failures.

This reply passes: "The job may have been cancelled. Retry if needed."
This reply fails: "The job may have been cancelled. Retry if the job was cancelled."
