---
type: llm
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if each sentence of the rewrite states one instruction or action, with at most one condition. A sentence with one action and one condition passes. A sentence with two actions or with two conditions fails.
A sentence with a single condition, a split sentence, and a rewrite with more sentences than the source are not failures. One verb with two objects is one action, so "it overrides the frontmatter and the default" passes.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times."
This reply fails: "The function retries up to 3 times and then returns an error."
