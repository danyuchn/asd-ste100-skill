---
type: llm
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if the rewrite has no phrasal verb, such as "times out", "is used to" (a verb with a particle), "spin up", or "kick off".
A phrasal verb that sits in code, an identifier, or a quoted string is not a failure.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "This function gets the latest metrics. If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times."
This reply fails: "If the request times out after 30 seconds, the function retries the request up to 3 times."
