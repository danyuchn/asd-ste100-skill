---
type: llm
---

Source: "Our blazing-fast CLI seamlessly integrates with your existing CI pipelines, empowering teams to effortlessly kick off builds and dive into logs without ever leaving the terminal."

Pass only if each sentence of the rewrite has 25 words or fewer.
Ignore each line that starts with `Kept as-is:`. Count the words of each sentence of the rewrite. Fail when any sentence is over 25 words.
A short sentence, a split sentence, and a rewrite with more sentences than the source are not failures.

This reply passes: "The CLI works with your existing CI pipelines. Teams can start builds and read logs without leaving the terminal."
This reply fails: "The CLI works with your existing CI pipelines, and it lets teams start builds and read the logs of those builds without ever leaving the terminal on their own machines."
