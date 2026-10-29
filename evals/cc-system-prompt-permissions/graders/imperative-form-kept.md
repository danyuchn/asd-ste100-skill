---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if the rewrite gives the two instructions to the agent in the imperative form ("do not call ...", "think about ...", "adjust ..."), not in a statement about the agent.
A split instruction and a different one-word verb are not failures.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "Do not call the exact same tool again. Think about why the user denied the tool call. Then adjust your approach."
This reply fails: "The agent does not call the exact same tool again. The agent thinks about why the user denied it."
