---
type: llm
weight: 2
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if the rewrite says that the function retries up to 3 times after a timeout, and returns an error to the caller after the retries, unless the config disables retries.
A split sentence and a named actor are not failures. A rewrite that returns the error before the retries fails.

This reply passes: "If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times. Then it returns an error to the caller. The function does not retry if the config disables retries."
This reply fails: "If the request reaches its timeout, the function returns an error to the caller."
