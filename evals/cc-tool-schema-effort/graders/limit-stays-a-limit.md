---
type: llm
weight: 2
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if the rewrite sets the field only when the user, or instructions such as `CLAUDE.md` or a skill, explicitly ask for a specific effort level.
A split sentence and a reworded condition are not failures. A sentence that drops "or instructions such as CLAUDE.md or a skill" fails.

This reply passes: "Set this field only when the user, or an instruction such as `CLAUDE.md` or a skill, explicitly asks for a specific effort level."
This reply fails: "Set this field when the task is hard."
