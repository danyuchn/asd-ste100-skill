---
type: llm
---

The source is: "Read the file config.yaml. Find the key timeout. Set its value to 30."

The source already follows the STE rules: three short imperative sentences, one instruction each.

Pass only if the response says that the text already follows the rules, or returns it with no change in meaning and at most small changes in wording. Fail if the response adds a step, a check, a condition, or an explanation that the source does not state, or changes `config.yaml`, `timeout`, or `30`.
