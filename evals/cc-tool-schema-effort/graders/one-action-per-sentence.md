---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if each sentence of the rewrite states one instruction or action, with at most one condition. A sentence with one action and one condition passes. A sentence with two actions or with two conditions fails.
A sentence with a single condition, a split sentence, and a rewrite with more sentences than the source are not failures.
These three forms each count as one action, because they state one event about one subject:
- One verb with two objects: "it overrides the frontmatter and the default" passes.
- Two alternative verbs with one object and one subject: "the agent reads or writes the file" passes.
- Two alternative subjects with one verb: "the frontmatter or the setting selects the model" passes.
A sentence fails when it joins two clauses that have different subjects or different events, such as "you omit the field and the agent picks its own effort".
A restrictive relative clause is part of the sentence it modifies, not a second action or a second condition.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "Set this field only when the user explicitly asks that this agent or its delegated work run at a specific effort level."
This reply fails: "Set this field when the user asks for it and omit the field when the user does not ask for it."
