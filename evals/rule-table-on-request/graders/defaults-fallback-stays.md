---
type: llm
weight: 2
---

Source: "The config file should be checked by the operator before the service is spun up; otherwise the defaults will be used."

Pass only if the rewrite keeps the fallback: the service uses the defaults when the operator does not check the file.
A split sentence and a named actor for "will be used" ("the service uses the defaults") are not failures.

This reply passes: "The operator should check the config file before the service starts. Otherwise the service uses the defaults."
This reply fails: "The operator should check the config file before the service starts."
