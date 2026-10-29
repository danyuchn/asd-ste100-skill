---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if each sentence of the rewrite has 25 words or fewer.
Ignore each line that starts with `Kept as-is:`. Count the words of each sentence of the rewrite. Fail when any sentence is over 25 words.
A short sentence, a split sentence, and a rewrite with more sentences than the source are not failures.

This reply passes: "This model override is optional. It takes precedence over the agent definition's `model` frontmatter and over the configured default subagent model."
This reply fails: "If you omit the override, the agent uses the model of the agent definition, and otherwise it uses the default model, which inherits from the parent unless a default subagent model is configured."
