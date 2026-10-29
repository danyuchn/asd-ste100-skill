---
type: llm
weight: 2
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if the rewrite says that the override takes precedence over both the agent definition's `model` frontmatter and the configured default subagent model.
A split sentence and a reworded "takes precedence over" are not failures. A rewrite that names only one of the two fails.

This reply passes: "The override takes precedence over the `model` frontmatter of the agent definition and over the configured default subagent model."
This reply fails: "The override takes precedence over the `model` frontmatter of the agent definition."
