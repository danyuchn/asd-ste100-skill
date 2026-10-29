---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if the rewrite says that the field is ignored for `subagent_type: "fork"`, and that a fork runs at the caller's own effort.
"your own effort" and "the caller's own effort" mean the same thing.

This reply passes: "The field is ignored for `subagent_type: "fork"`. A fork runs at your own effort."
This reply fails: "The field is ignored for `subagent_type: "fork"`."
