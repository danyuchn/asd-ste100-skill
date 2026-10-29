---
type: llm
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if no sentence of the rewrite keeps a passive verb when the source names the actor of that verb. A passive sentence such as "the user will be prompted" or "an error is returned to the caller by the function" fails. An active sentence such as "the user receives a prompt" passes.
A passive verb whose actor the source does not name is not a failure.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "This function gets the latest metrics from the monitoring backend. If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times. Then it returns an error to the caller. The function does not retry if the config disables retries."
This reply fails: "The latest metrics are fetched by this function. Retries are disabled in the config."
