---
type: llm
---

Source: "The config file should be checked by the operator before the service is spun up; otherwise the defaults will be used."

Pass only if the response names or fixes the passive voice ("should be checked by the operator", "will be used"), as a violation or as an advisory finding.
The response may name the passive voice in a table row, in a finding, or in the rewrite.

This reply passes: "| Active voice | The config file should be checked by the operator | The operator should check the config file |"
This reply fails: "| Simple tenses | will be used | uses |  (no mention of the passive voice anywhere)"
