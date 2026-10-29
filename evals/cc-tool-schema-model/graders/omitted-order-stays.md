---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if when the override is omitted, the rewrite says that the agent uses the agent definition's model first and the default second.
A split sentence and "else" or "otherwise" for the second step are not failures.

This reply passes: "If you omit the override, the agent uses the model of its agent definition. Otherwise it uses the default."
This reply fails: "If you omit the override, the agent uses the default first and then the model of its agent definition."
