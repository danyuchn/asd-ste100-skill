---
type: llm
weight: 2
---

Source: "The installer should be run by the operator; it runs `cd /tmp && ls; echo done` and then spins up the daemon."

Pass only if the operator is the subject of an active sentence that runs the installer.
The "should" and the daemon start are checked by other graders, so a rewrite that changes them is not a failure here.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "The operator should run the installer. The installer runs `cd /tmp && ls; echo done`. Then the installer starts the daemon."
This reply fails: "The installer should be run by the operator. The installer runs `cd /tmp && ls; echo done`."
