---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if the rewrite adds no fact or cause that the source does not state. An added cause, an added number, an added step, or an added condition fails.
A reworded source fact, a split sentence, a new sentence order, and a named actor that the source names are not added facts. A condition that the rewrite states in two steps is not an added fact: the source states that the permission mode or the permission settings can allow a call automatically, so a sentence for the automatic allowance and a sentence for the case where neither allows the call both come from the source.

Ignore each line that starts with `Kept as-is:`. The `kept-as-is-reason` grader judges those lines.

This reply passes: "Tools run in a permission mode that the user selects. The user's permission mode or permission settings can automatically allow a tool call. When neither allows your tool call, the user sees a prompt. The user can then approve or deny the call. If the user denies a tool call, do not try the exact same tool call again. Instead, think about why the user denied the call. Then change your approach."
This reply fails: "Tools run in a permission mode that the user selects. The user receives a prompt, because tools can change files. The user can approve or deny the execution."
