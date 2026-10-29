---
type: llm
---

Source: "The upload might have been rejected because the file could possibly exceed the size limit that has been configured for this workspace, or the token may have expired; try again later."

Pass only if each sentence of the rewrite has 25 words or fewer.
Ignore each line that starts with `Kept as-is:`. Count the words of each sentence of the rewrite. Fail when any sentence is over 25 words.
A short sentence, a split sentence, and a rewrite with more sentences than the source are not failures.

This reply passes: "The upload might have been rejected. The file could exceed the size limit of this workspace, or the token may have expired. Try again later."
This reply fails: "The upload might have been rejected because the file could possibly exceed the size limit that you configured for this workspace, or because the token may have expired."
