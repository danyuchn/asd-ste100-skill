---
type: llm
weight: 2
---

Source: "Set the request timeout to 30 seconds, and then the worker pool size to 4, before you start the job. (An invisible character sits between "worker" and "pool".)"

Pass only if each sentence of the rewrite states one action, the timing ("before you start the job") still governs both settings, and the response adds no sentence, step, condition, or caveat that the source does not state.
A sentence that names an action of the source is not an addition. A reply with more sentences than the source is not a failure by its count.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "1. Set the request timeout to 30 seconds.
2. Set the worker pool size to 4.
3. Start the job."
This reply fails: "Do these two steps before you start the job. First, set the request timeout to 30 seconds. Then set the worker pool size to 4."
This reply also fails, because it adds a sentence: "Before you start the job, set the request timeout to 30 seconds. Then set the worker pool size to 4. Do not start the job until both changes are made."
This reply also fails, because the line above the list introduces the list, and the source states no such instruction: "Do these steps in order:
1. Set the request timeout to 30 seconds.
2. Set the worker pool size to 4.
3. Start the job."
A number, a period, and the text of one step are one sentence of the list, and they are no addition.
