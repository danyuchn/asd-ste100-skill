---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Judge only the lines that start with `Kept as-is:`. Ignore the rewrite above them.

Pass when the reply has no such line, or when each reason states the precision that the kept phrase carries.
A reason fails when it makes a claim that the source does not state. A reason also fails when it describes the writer's own work, such as a word count, a sentence count, or a rule that the writer applied.

A reason can state what the kept word excludes, because the exclusion is the precision. "explicitly: an implied request does not count." passes.

A reason can state the actor that the source leaves out of a kept passive, because that absence is what the phrase carries. "is ignored: the source names no actor that ignores the field." passes.

A kept character, a kept letter case, and a kept punctuation mark each carry a form. A reason for one of them states what the form carries, such as emphasis, and it passes.

These reasons pass:
- "exact same tool call: only an identical call is prohibited." It states the scope of the prohibition that the source gives.
- "exact same tool call: a call with a change is a different call." It defines the kept phrase and adds no permission.
- "neither of them allows: the prompt needs both of them to not allow the call." It states the condition that the source gives.

These reasons fail:
- "exact same: a changed call is permitted." The source grants no permission for a changed call.
- "7 sentences: the 20-word cap needs one action for each sentence." It reports the writer's own work.
- "is ignored: the source names no actor and gives no subject to recast it to." The recast is a rule of the writer.
- "the default subagent model is set by the user, not by the agent." The source names no actor who sets it.
