---
type: llm
---

Source: "The nightly sync may have skipped some records, and the dashboard could be showing stale counts, which might sometimes persist until the next run, likely because the cache is occasionally not invalidated."

Pass only if each sentence of the response states one claim and has 25 words or fewer.
A short sentence, a split sentence, and a hedge kept in its own sentence are not failures.
Ignore each line that starts with `Kept as-is:` when you judge the form of the sentences.

This reply passes: "The nightly sync may have skipped some records. The dashboard could show stale counts. These stale counts might sometimes stay until the next run. The likely cause is that the cache is occasionally not invalidated."
This reply fails: "The nightly sync may have skipped some records, and the dashboard could show stale counts, which might sometimes stay until the next run."
