---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if each sentence of the rewrite states one instruction or action, with at most one condition. A sentence with one action and one condition passes. A sentence with two actions or with two conditions fails.
A sentence with a single condition, a split sentence, and a rewrite with more sentences than the source are not failures.
These three forms each count as one action, because they state one event about one subject:
- One verb with two objects: "it overrides the frontmatter and the default" passes.
- One verb with two objects that each repeat the preposition: "it takes precedence over the frontmatter and over the default" passes.
- Two alternative verbs with one object and one subject: "the user can approve or deny the call" passes.
- Two alternative subjects with one verb: "the permission mode or the permission settings can allow the call" passes.
A negated form counts like its positive form, so "sometimes the permission mode or the permission settings do not allow a tool automatically" states one event and passes.
A sentence fails when it joins two clauses that have different subjects or different events, such as "the user approves the call and the tool runs it".
A restrictive relative clause is part of the sentence it modifies, not a second action or a second condition.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "Tools run in a permission mode that the user selects. The user's permission mode or permission settings can automatically allow a tool call. When neither allows your tool call, the user sees a prompt. The user can then approve or deny the call. If the user denies a tool call, do not try the exact same tool call again. Instead, think about why the user denied the call. Then change your approach."
This reply fails: "The user approves the call and then the tool runs it, or the user denies the call and you adjust your approach."
