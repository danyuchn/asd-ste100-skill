---
type: llm
weight: 2
---

Source: "The job may have been cancelled; retry if needed."

Pass only if the rewrite states the cancellation as possible and not as a fact.
A hedge of the same strength (may, might, could) and a split sentence are not failures.

This reply passes: "The job may have been cancelled. Retry if needed."
This reply fails: "The job was cancelled. Retry it."
