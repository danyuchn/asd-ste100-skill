---
type: llm
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if the rewrite adds no fact, number, or behavior that the source does not state. An added cause, an added number, an added step, or an added condition fails.
A reworded source fact, a split sentence, a new sentence order, and a named actor that the source names are not added facts.

This reply passes: "This function gets the latest metrics from the monitoring backend. If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times. Then it returns an error to the caller. The function does not retry if the config disables retries."
This reply fails: "This function gets the latest metrics. If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times. The function logs each retry."
