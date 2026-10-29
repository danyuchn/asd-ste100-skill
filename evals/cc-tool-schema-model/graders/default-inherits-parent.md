---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if the rewrite says that the default inherits from the parent, unless a default subagent model is configured.
A split sentence and a reworded condition are not failures.

This reply passes: "The default model inherits from the parent, unless a default subagent model is configured."
This reply fails: "The default model always inherits from the parent."
