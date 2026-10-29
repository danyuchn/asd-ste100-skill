---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Judge only the lines that start with `Kept as-is:`. Ignore the rewrite above them.

Pass when the reply has no such line, or when each reason states the precision that the kept phrase carries.
A reason fails when it makes a claim that the source does not state. A reason also fails when it describes the writer's own work, such as a word count, a sentence count, or a rule that the writer applied.

A reason can state what the kept word excludes, because the exclusion is the precision. "explicitly: an implied request does not count." passes.

A kept character, a kept letter case, and a kept punctuation mark each carry a form. A reason for one of them states what the form carries, such as emphasis, and it passes.

These reasons pass:
- "is configured: the source does not name the actor who configures the default." It states what the kept phrase leaves open.
- "always: the fork takes the parent model in every case." It states the strength of the kept word.

These reasons fail:
- "4 sentences, about 75 words: the 25-word cap would drop a fact." It reports the writer's own work.
- "optional: the field has a default value of inherit." The source names no such default value.
- "subagent_type: \"fork\": the exact value that the harness checks." The source names no harness.
