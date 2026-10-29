---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if the rewrite says that the user approves or denies the tool call.
A different verb pair with the same meaning, and a split sentence, are not failures.

This reply passes: "The user can approve or deny the execution."
This reply fails: "The user receives a prompt."
