---
type: llm
---

Source: "The config file should be checked by the operator before the service is spun up; otherwise the defaults will be used."

Pass only if the rewrite names the operator as the actor who checks the config file.
"should" in the rewrite is not a failure.

This reply passes: "The operator should check the config file before the service starts."
This reply fails: "The config file should be checked before the service starts."
