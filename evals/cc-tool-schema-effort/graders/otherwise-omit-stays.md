---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if for the otherwise case, the rewrite says to omit the field and that the agent runs at its usual effort.
A split sentence and "then" or "in that case" in place of "otherwise" are not failures.

This reply passes: "Otherwise, omit the field. The agent then runs at its usual effort."
This reply fails: "Otherwise, omit the field."
