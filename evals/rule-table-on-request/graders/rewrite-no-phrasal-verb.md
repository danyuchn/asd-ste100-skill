---
type: llm
---

Source: "The config file should be checked by the operator before the service is spun up; otherwise the defaults will be used."

Pass only if the rewrite column has no phrasal verb, such as "spun up".
A phrasal verb in the Original column is not a failure.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "| Phrasal verbs | spun up | starts |"
This reply fails: "The operator should check the config file before the service is spun up."
