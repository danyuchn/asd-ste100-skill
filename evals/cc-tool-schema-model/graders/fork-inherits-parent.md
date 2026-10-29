---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if the rewrite says that the field is ignored for `subagent_type: "fork"`, and that a fork always inherits the parent model.
A split sentence is not a failure.

This reply passes: "The field is ignored for `subagent_type: "fork"`. A fork always inherits the parent model."
This reply fails: "A fork uses the model that this field sets."
