---
type: llm
---

Source: "Optional model override for this agent. Takes precedence over the agent definition's model frontmatter and the configured default subagent model. If omitted, uses the agent definition's model, else the default (inherits from the parent unless a default subagent model is configured). Ignored for subagent_type: "fork" — forks always inherit the parent model."

Judge only the lines that start with `Kept as-is:`. Ignore the rewrite above them.

Pass when the reply has no such line, or when each reason states the precision that the kept phrase carries.
A reason fails when it makes a claim that the source does not state. A reason also fails when it describes the writer's own work, such as a word count, a sentence count, or a rule that the writer applied.

A reason can state what the kept word excludes, because the exclusion is the precision. "explicitly: an implied request does not count." passes.

A reason can state the actor that the source leaves out of a kept passive, because that absence is what the phrase carries. "is ignored: the source names no actor that ignores the field." passes.

A reason can state the current relevance that a kept compound tense carries, because that relevance is why the tense stays. "has denied: the denial still applies when you adjust your approach." passes.

A kept character, a kept letter case, and a kept punctuation mark each carry a form. A reason for one of them states what the form carries, such as emphasis, and it passes.

A reason can name what a kept phrase of precision decides. "takes precedence over: the order of the sources decides the model." passes. The source gives the override priority over the frontmatter and over the configured default, and it then names the default, so the three sources stand in an order. The reason adds no actor and no outcome.

These reasons pass:
- "is configured: the source does not name the actor who configures the default." It states what the kept phrase leaves open.
- "always: the fork takes the parent model in every case." It states the strength of the kept word.

These reasons fail:
- "4 sentences, about 75 words: the 25-word cap would drop a fact." It reports the writer's own work.
- "optional: the field has a default value of inherit." The source names no such default value.
- "subagent_type: \"fork\": the exact value that the harness checks." The source names no harness.
- "is ignored: the source names no actor and gives no subject to recast it to." The recast is a rule of the writer.
- "the default subagent model is set by the user, not by the agent." The source names no actor who sets it.
