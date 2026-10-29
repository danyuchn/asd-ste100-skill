---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if the rewrite says that the override is optional.
"You can omit it" or "you do not have to set it" counts as optional.

This reply passes: "This model override is optional."
This reply fails: "Set this model override for each agent."
