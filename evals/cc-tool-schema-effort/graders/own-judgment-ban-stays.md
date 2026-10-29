---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if the rewrite forbids setting the field on the agent's own judgment.
Different words for "never" and "your own judgment" are not failures.

This reply passes: "Never set this field on your own judgment."
This reply fails: "Set this field when you judge that the task needs it."
