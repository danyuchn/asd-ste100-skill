---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if no sentence of the rewrite keeps a passive verb when the source names the actor of that verb. A passive sentence such as "the user will be prompted" or "the file should be checked by the operator" fails. An active sentence such as "the user receives a prompt" passes.
A passive verb whose actor the source does not name is not a failure.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "Tools run in a permission mode that the user selects. When you call a tool that the user's permission mode or permission settings do not allow automatically, the user receives a prompt. The user can approve or deny the execution."
This reply fails: "Tools run in a permission mode that the user selects. When you call a tool that the settings do not allow automatically, the user will be prompted."
