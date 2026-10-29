---
type: llm
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if each sentence of the rewrite has 25 words or fewer.
Ignore each line that starts with `Kept as-is:`. Count the words of each sentence of the rewrite. Fail when any sentence is over 25 words.
A short sentence, a split sentence, and a rewrite with more sentences than the source are not failures.

This reply passes: "This function gets the latest metrics from the monitoring backend. If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times."
This reply fails: "This function gets the latest metrics from the monitoring backend, and if the request reaches its timeout of 30 seconds, it retries the request up to 3 times before it returns an error."
