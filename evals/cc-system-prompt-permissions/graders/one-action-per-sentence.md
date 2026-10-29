---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if each sentence of the rewrite states one instruction or action, with at most one condition. A sentence with one action and one condition passes. A sentence with two actions or with two conditions fails.
A sentence with a single condition, a split sentence, and a rewrite with more sentences than the source are not failures. One verb with two objects is one action, so "it overrides the frontmatter and the default" passes.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "Tools run in a permission mode that the user selects. The user's permission mode or permission settings can automatically allow a tool call. When neither allows your tool call, the user sees a prompt. The user can then approve or deny the call. If the user denies a tool call, do not try the exact same tool call again. Instead, think about why the user denied the call. Then change your approach."
This reply fails: "The user approves the call and then the tool runs it, or the user denies the call and you adjust your approach."
