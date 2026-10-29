---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Pass only if the rewrite adds no fact, cause, or number that the source does not state. An added cause, an added number, an added step, or an added condition fails.
A reworded source fact, a split sentence, a new sentence order, and a named actor that the source names are not added facts.

This reply passes: "This model override is optional. It takes precedence over the `model` frontmatter of the agent definition and over the configured default subagent model. If you omit it, the agent uses the model of its agent definition, else the default. The field is ignored for `subagent_type: "fork"`. A fork always inherits the parent model."
This reply fails: "This model override is optional. It takes precedence over the agent definition. A smaller model makes the agent faster."
