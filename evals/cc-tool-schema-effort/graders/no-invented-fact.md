---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if the rewrite adds no fact, cause, or number that the source does not state. An added cause, an added number, an added step, or an added condition fails.
A reworded source fact, a split sentence, a new sentence order, and a named actor that the source names are not added facts.

Ignore each line that starts with `Kept as-is:`. The `kept-as-is-reason` grader judges those lines.

This reply passes: "Set this field only when the user explicitly asks that this agent or its delegated work run at a specific effort level. Never set it on your own judgment. Otherwise omit it, and the agent runs at its usual effort. The field is ignored for `subagent_type: "fork"`. A fork runs at your own effort."
This reply fails: "Set this field only when the user explicitly asks for a specific effort level. A higher effort level costs more tokens."
