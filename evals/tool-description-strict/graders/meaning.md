---
type: llm
weight: 2
---

The response is a rewrite of this tool description: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if all of these are true:

1. These facts are all present and unchanged: the latest metrics, the monitoring backend, a timeout after 30 seconds, up to 3 retries, an error to the caller after the retries, and no retries when the config disables them.
2. Each sentence states one action or one condition, and has 25 words or fewer.
3. The sentences use active voice. Each one names the actor, such as "the function", except where the actor is unknown.
4. The text has no semicolon, no present perfect such as "have been disabled", and no phrasal verb.
5. The rewrite adds no fact, number, or behavior that the source does not state.
6. The response is the rewritten text alone. Last lines that start with "Kept as-is:" are allowed.
