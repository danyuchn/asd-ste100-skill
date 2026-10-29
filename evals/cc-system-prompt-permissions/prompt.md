---
tags: [strict]
max_turns: 6
allowed_tools: [Read, Skill, Bash]
---

Disambiguate this paragraph of a system prompt:

Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach.
