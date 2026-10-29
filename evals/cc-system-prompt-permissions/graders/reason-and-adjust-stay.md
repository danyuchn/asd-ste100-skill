---
type: llm
---

Source: "Tools are executed in a user-selected permission mode. When you attempt to call a tool that is not automatically allowed by the user's permission mode or permission settings, the user will be prompted so that they can approve or deny the execution. If the user denies a tool you call, do not re-attempt the exact same tool call. Instead, think about why the user has denied the tool call and adjust your approach."

Pass only if the rewrite tells the agent to think about the reason for the denial and to adjust its approach.
Different words for "think about" and "adjust" are not failures.

This reply passes: "Think about why the user denied the tool call. Then adjust your approach."
This reply fails: "Do not call the exact same tool again."
