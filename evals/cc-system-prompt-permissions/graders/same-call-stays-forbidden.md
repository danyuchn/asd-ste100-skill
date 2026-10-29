---
type: llm
weight: 2
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if after a denial, the rewrite forbids the exact same tool call again.
A different word for "re-attempt" is not a failure.

This reply passes: "If the user denies a tool call, do not call the exact same tool again."
This reply fails: "If the user denies a tool call, call the tool again with the same input."
