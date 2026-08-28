---
name: asd-ste100
description: "Use before you write new text, and before you revise existing text, that a reader must not misread. The trigger is the act of writing, not only a request to fix text that already exists. Applies to text a machine parses (tool descriptions, error messages, inter-agent instructions, system prompts, status reports) and to prose a person reads (PR descriptions, commit messages, issue bodies, design docs, plans, code review comments, docstrings, code comments, READMEs, changelogs). Also use it when text reads as dense, hedged, or easy to misparse. Triggers: write the PR description, write the commit message, draft the design doc, write this docstring, write this error message, disambiguate, STE100 rewrite, apply Simplified Technical English, plain-language rewrite, controlled-language rewrite, rewrite so an agent cannot misread this. Not for creative or marketing copy."
version: 0.5.2
---

# Simplified Technical English (ASD-STE100)

ASD-STE100 removes the two biggest sources of misreading: words with more than one meaning, and sentences with more than one possible structure. This skill borrows that discipline for any reader who cannot ask a question. That is a **machine** parsing an error message or a tool description, and a **person** reading a design doc after the author moved on.

STE is an **authoring** standard, not a cleanup tool. Use it to write the first draft. Use it again to revise a draft that exists.

## When to Use This Skill

**Before you write.** The rules shape the first draft. Do not write loose prose and plan a cleanup pass.

**Before you revise.** Text reads as dense, hedged, or easy to misparse, and misreading has a real cost. Ask for a before/after rule table if you want to see which rules it broke.

Not for creative or marketing copy. STE is flat and literal by design.

## Two Questions Before You Start

Answer both. They are independent, and together they select the process and the strictness.

### 1. Do you write or revise?

**Write path** — no input text exists. You produce the text. Apply the Core Rules as you write each sentence, then scan your own draft before you output it.

**Revise path** — an input text exists. Scan it, flag each violation, and fix each one without changing what the text says.

The rules are identical on both paths. The hazard is not. On the revise path you can lose a fact or weaken a hedge that the source stated. On the write path there is no source to stay faithful to, so the hazard inverts: you can assert something you never checked. See Process for the step that guards each one.

### 2. Who reads it — a machine or a person?

This picks the mode. If the user does not say which, infer from the text type and state the choice in one line.

**Strict** — procedures, error messages, tool and function descriptions, inter-agent instructions, safety text. Anywhere a wrong reading has a cost. Apply every rule below, including the hard length caps and one-word-one-meaning discipline.

**STE-flavored** — READMEs, PR descriptions, changelogs, explanatory prose. Apply the structural rules in full and treat the lexical rules as advisory (see Core Rules for that split). In practice that means keeping the sentence length caps, active voice, simple tenses, no phrasal verbs, no semicolons, no nominalization and no marketing adjectives, while dropping the one-word-one-meaning lockdown: prose needs some range, and a strict rewrite of prose reads as a personality transplant rather than a clarification.

## Source and Scope

This skill encodes the rule categories of ASD-STE100 Issue 9 (Jan 2025). It does **not** reproduce ASD's ~900-word approved dictionary, which is not free to redistribute. It applies the underlying principle instead: pick the plainest, most common word available, and use it the same way every time. When exact approved wording matters, check word-by-word against the real dictionary. See `references/writing-rules.md` for the rule summary, the redistribution terms, and how to request the standard.

## Core Rules

One rule set covers both paths. On the write path the rules constrain the sentence you produce. On the revise path they are what you scan the input for.

**Structural rules** describe sentence shape. Apply them with confidence. **Lexical rules** are defined by the dictionary this skill does not have, so apply them as a direction of travel. Never imply dictionary compliance you cannot verify.

### Structural rules — apply these

| Rule | Do | Don't |
|---|---|---|
| Active voice | "The agent deletes the file." | "The file is deleted (by the agent)." — unless the actor is genuinely unknown or irrelevant |
| No phrasal verbs (Rule 9.3) | "Remove the panel." / "Start the job." | "Take off the panel." / "Spin up the job." — a two-word verb has meanings the parts do not predict |
| One instruction per sentence | "Open the file. Read line 3." | "Open the file and read line 3, then check if it matches." |
| Sentence length | ≤20 words for instructions/procedures, ≤25 words for descriptions | Long compound/subordinate-clause sentences |
| No semicolons (Rule 8.1) | Split into separate sentences | Any semicolon at all — STE bans the mark outright, not only as a clause join. (Rule 8.1 permits every other standard punctuation mark. The em dash is *not* banned by STE, though it often signals a sentence that should be split.) |
| Noun clusters | ≤3 words stacked as a noun phrase ("fuel pump valve") | 4+ word noun stacks ("high pressure fuel pump inlet valve assembly") |
| No ellipsis | Keep the subject, verb, and article explicit even if it reads longer | Drop words to save space ("Files not backed up will be lost" → ambiguous which files) |
| Keep modality | Write path: pick the hedge that matches your evidence. Revise path: "The request **may have** failed." stays "may have" | Write path: state a certainty you did not check. Revise path: promote a hedge to a fact ("The request failed.") |
| Paragraph limits | One topic per paragraph, ≤6 sentences | Multi-topic paragraphs |
| Lists for sequences | Use a numbered or bulleted list for 3+ steps or conditions | Bury a sequence inside one prose sentence |

### Lexical rules — direction of travel only

| Rule | Do | Don't |
|---|---|---|
| One word, one meaning | Pick one verb for one action and reuse it every time (always "check", never mix "check"/"verify"/"confirm" for the same action) | Rotate synonyms for the same idea across a document |
| One part of speech per word | "Apply oil to the valve" (oil = noun) | "Oil the valve" (oil = verb) |
| Verb, not noun (Rule 3.7) | "Analyze the log." | "Perform an analysis of the log." — the noun form hides who acts |
| Domain terms | Keep necessary technical terms, but define each one once if not common English | Use jargon without ever defining it |

### Simple tenses — apply with one exception

STE permits infinitive, imperative, simple present, simple past, simple future, and past participle as adjective. It excludes present perfect and other compound forms: "we received the report", not "we have received the report".

"The job has completed" (its output is available now) and "the job completed" (at some past point) are different statements. **Where the compound form carries information the simple form cannot — current relevance, or a hedge as in "may have failed" — keep it and flag the departure.** Elsewhere, follow the rule.

## Scan Checklist

These six habits cover most of what makes machine-written English hard to parse. Each one is mechanical: you can point at the exact word or punctuation mark that breaks the rule, with no judgment call.

Scan for all six on both paths. On the revise path, scan the input before you change it. On the write path, scan your own draft before you output it — your first draft has these habits too.

1. **Synonym rotation** — the same thing gets several names in one document ("the user", "the customer", "the client"). The reader cannot tell whether they are one thing or three. Fix: pick one name, use it every time.
2. **Hedge stacking** — helper verbs and qualifiers pile up until the sentence asserts nothing ("it is important to note that this may potentially help to improve"). Fix: state the claim, or delete it.
3. **Nominalization** — an action frozen into a noun ("perform an analysis of", "provides assistance to"). Fix: use the verb ("analyze", "helps").
4. **Marketing adjectives** — words that claim quality instead of showing it: seamless, robust, powerful, cutting-edge, effortless, blazing-fast. Fix: delete, or replace with the measurement that earns the claim.
5. **Run-on sentences** — several ideas joined by semicolons or em dashes. Fix: one idea per sentence.
6. **Soft phrasal verbs** — spin up, reach out, dive into, kick off. Fix: use the single plain verb (start, contact, read, begin).

## Process

Pick the path from Question 1, then follow that process. Both start by picking the mode.

### Write path

1. Pick the mode (Strict or STE-flavored) from the kind of text you must produce.
2. List the facts the text must carry. Mark each one as checked or inferred. You are the source, so nothing else records the difference.
3. Write the text. Apply the Core Rules to each sentence as you write it.
4. **Match every hedge to your evidence.** A short, active, single-meaning sentence can still be false. Write "I did not run it" rather than a confident sentence you cannot support. The length caps push toward confident phrasing, so check the inferred facts from step 2 one more time here.
   - **Check that every number you state appears in your evidence.** A value you chose between tested points is not a tested value. Name which it is.
   - **Say what a measurement does not cover.** A number from a small or self-chosen sample is evidence about that sample. Name the limit.
5. Run the Scan Checklist over your own draft. Fix what it finds.
6. Output the text (see Output Format). Keep the mode choice and the rule analysis internal.

### Revise path

1. Pick the mode (Strict or STE-flavored). Say which only when the user asked for the rule table — see Output Format.
2. Read the input text once for meaning — do not start rewriting before you understand what it must still say afterward.
3. Walk it sentence by sentence. Flag every rule violation from the Core Rules tables and every habit from the Scan Checklist. In STE-flavored mode, flag the lexical rules but do not enforce them.
4. Rewrite each flagged sentence to fix the violation while preserving the original meaning exactly. If a rewrite would drop necessary precision (a safety condition, a scope qualifier, a number), keep the longer phrasing and flag it instead of silently simplifying.
   - **Check modality before you commit to a rewrite.** Hedges ("may", "could", "sometimes", "is likely to") carry the author's confidence, and confidence is content. A shorter sentence that upgrades a hedge to a fact is not a simplification — it is a different claim. This is the most common way a well-intentioned STE rewrite goes wrong, because hedges are exactly what a length cap tempts you to cut.
   - Never add a fact the source did not state. A rewrite that reads better because it supplies a cause, a frequency, or a mechanism has stopped being a rewrite.
5. Output the rewritten text (see Output Format). Keep the mode choice and the rule analysis internal unless the user asked to see them.
6. If the input already complies, say so — do not force changes onto compliant text.

## Output Format

**Default: the text, and nothing else.** Most callers want a result they can paste straight into a tool description, an error string, a PR description, or a prompt. Print the text on its own. Do not add a preamble about this skill, a mode announcement, a violation count, a summary of what changed, a rule table, or a closing offer to explain further.

The one permitted addition, on the revise path: if step 4 kept a longer phrasing on purpose, add a single line after the text, prefixed `Kept as-is:`, naming the phrase and the precision that would have been lost. Omit the line when there is nothing to report.

**On request: the rule table.** This applies to the revise path only. The write path has no "before", so it has no diff to show. When the user asks to see the reasoning — "show the diff", "which rules did it break", "explain the changes", "before/after" — output this table instead:

```markdown
| Rule violated | Original | Simplified |
|---|---|---|
| Present perfect tense | "We have received your request." | "We received your request." |
| Noun cluster (4+ words) | "the agent task queue priority handler" | "the handler that sets task-queue priority" |

Mode: Strict. 7 violations found.
```

Follow the table with a one-line note on anything you deliberately did **not** simplify, and why (usually: simplifying would lose required precision).

## Boundaries

This skill will not:

- Reproduce ASD's dictionary from memory. Treat the official download as the source of truth for exact approved wording.
- Simplify creative, marketing, or persuasive copy where voice and nuance are the point.
- Silently drop a safety condition, exception, or scope qualifier to shorten a sentence. Flag the trade-off instead.
- Guarantee an aerospace-grade STE-compliant document. This is a clarity tool inspired by STE, not a certified STE authoring tool.
- Make weak content true or useful. STE fixes the *form* of a text, not its substance. A hollow paragraph rewritten under these rules becomes a clean, short, well-punctuated hollow paragraph. On the write path the same limit becomes a trap: a clean sentence reads as a checked one, so state what you verified and how. If the text has nothing to say, say so instead of polishing it.
- Shorten past the point of clarity. Cutting words is not the goal. Removing ambiguity is. Stop when the sentence is unambiguous, not when it is shortest.

## Additional Resources

- **`references/writing-rules.md`** — fuller summary of the 9 rule sections and dictionary structure, with citations to the official standard and secondary sources.
- **`examples/before-after.md`** — worked examples, including official STE examples and agent-output examples built for this skill.
