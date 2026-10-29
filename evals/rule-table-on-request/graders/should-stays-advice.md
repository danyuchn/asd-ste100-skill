---
type: llm
---

Source: "The config file should be checked by the operator before the service is spun up; otherwise the defaults will be used."

Pass only if the rewrite keeps "should" as a recommendation. A rewrite that turns it into an instruction to the operator fails.
A split sentence is not a failure.

This reply passes: "The operator should check the config file before the service starts."
This reply fails: "Check the config file before you start the service."
