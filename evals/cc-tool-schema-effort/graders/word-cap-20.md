---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Pass only if each sentence of the rewrite has 20 words or fewer.
Ignore each line that starts with `Kept as-is:`. Count the words of each sentence of the rewrite. Fail when any sentence is over 20 words.
A short sentence, a split sentence, and a rewrite with more sentences than the source are not failures.

This reply passes: "Set this field only when the user explicitly asks for a specific effort level. Otherwise omit it."
This reply fails: "Set this field only when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level."
