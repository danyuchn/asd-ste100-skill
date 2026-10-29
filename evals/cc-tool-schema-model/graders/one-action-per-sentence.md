---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if each sentence of the rewrite states one instruction or action, with at most one condition. A sentence with one action and one condition passes. A sentence with two actions or with two conditions fails.
A sentence with a single condition, a split sentence, and a rewrite with more sentences than the source are not failures. One verb with two objects is one action, so "it overrides the frontmatter and the default" passes.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "If you omit the override, the agent uses the model of its agent definition."
This reply fails: "If you omit the override and the agent definition has no model, the agent uses the default and inherits the parent model."
