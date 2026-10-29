---
type: llm
weight: 2
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if the rewrite prompts the user only when the permission mode or the permission settings do not allow the tool automatically.
A reworded condition, a split sentence, and a named actor are not failures.

This reply passes: "When you call a tool that the user's permission mode or permission settings do not allow automatically, the user receives a prompt."
This reply fails: "The user receives a prompt each time you call a tool."
