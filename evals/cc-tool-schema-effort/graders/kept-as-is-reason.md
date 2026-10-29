---
type: llm
---

Source: "Reasoning effort for this agent. Set this ONLY when the user, or instructions such as CLAUDE.md or a skill, explicitly ask that this agent or delegated work run at a specific effort level, never on your own judgment; otherwise omit it and the agent runs at its usual effort. Ignored for subagent_type: "fork": a fork runs at your own effort."

Judge only the lines that start with `Kept as-is:`. Ignore the rewrite above them.

Pass when the reply has no such line, or when each reason states the precision that the kept phrase carries.
A reason fails when it makes a claim that the source does not state. A reason also fails when it describes the writer's own work, such as a word count, a sentence count, or a rule that the writer applied.

A reason can state what the kept word excludes, because the exclusion is the precision. "explicitly: an implied request does not count." passes.

A reason can state the actor that the source leaves out of a kept passive, because that absence is what the phrase carries. "is ignored: the source names no actor that ignores the field." passes.

A reason can state the current relevance that a kept compound tense carries, because that relevance is why the tense stays. "has denied: the denial still applies when you adjust your approach." passes.

A kept character, a kept letter case, and a kept punctuation mark each carry a form. A reason for one of them states what the form carries, such as emphasis, and it passes.

These reasons pass:
- "ONLY: the field needs an explicit request." It states the scope of the kept word.
- "for this agent or for delegated work: the request can name either one." It states the scope that the source gives.
- "ONLY: the capitals keep the emphasis of the source." It states what the kept letter case carries.

These reasons fail:
- "the request can cover this agent or any delegated work." The word "any" widens the scope of the source.
- "ONLY: a higher effort level costs more tokens." The source states no cost.
- "is ignored: the source names no actor and gives no subject to recast it to." The recast is a rule of the writer.
- "the default subagent model is set by the user, not by the agent." The source names no actor who sets it.
