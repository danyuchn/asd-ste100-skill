---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if the rewrite names the user as the actor who selects the permission mode.
A relative clause ("a permission mode that the user selects") and a split sentence are not failures.

This reply passes: "Tools run in a permission mode that the user selects."
This reply fails: "Tools run in a permission mode that is set by default."
