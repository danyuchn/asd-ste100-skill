---
tags: [strict]
max_turns: 6
allowed_tools: [Read, Skill, Bash]
---

Apply STE100 to this tool input description from Claude Code:

Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model.
