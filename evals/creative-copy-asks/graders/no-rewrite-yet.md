---
type: llm
weight: 2
---

Source: "Dream it. Build it. Own the night."

Pass only if the response asks the user whether to rewrite the tagline, and gives no new tagline. The skill has an "Ask first" mode: creative or persuasive copy keeps its own style, so the skill asks the user first.

These are not failures: a sentence that says the tagline is creative copy, a sentence that names what a rewrite would lose, a quote of a phrase of the source, and an offer of the options that a rewrite could take. The response may ask more than one question.

The response fails only when it gives a new tagline, in whole or in part, such as "Imagine it. Build it. Control the night." or "Build your own product. Use it at night."

This reply passes: "Do you want me to rewrite this tagline in STE style? It is creative copy, so the rewrite will lose its rhythm and tone. If you want it, I can keep the same three-part structure or drop it for a plainer single sentence."

This reply fails: "Imagine it. Build it. Control the night."
