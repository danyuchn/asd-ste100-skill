---
type: llm
---

Source: "This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config."

Pass only if each sentence of the rewrite states one instruction or action, with at most one condition. A sentence with one action and one condition passes. A sentence with two actions or with two conditions fails.
A sentence with a single condition, a split sentence, and a rewrite with more sentences than the source are not failures.
These three forms each count as one action, because they state one event about one subject:
- One verb with two objects: "it overrides the frontmatter and the default" passes.
- Two alternative verbs with one object and one subject: "the agent reads or writes the file" passes.
- Two alternative subjects with one verb: "the frontmatter or the setting selects the model" passes.
A sentence fails when it joins two clauses that have different subjects or different events, such as "you omit the field and the agent picks its own effort".
A restrictive relative clause is part of the sentence it modifies, not a second action or a second condition.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "If the request reaches its timeout of 30 seconds, the function retries the request up to 3 times."
This reply fails: "The function retries up to 3 times and then returns an error."
