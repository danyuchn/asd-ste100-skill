---
name: rewrite
description: Rewrites English in ASD-STE100 Simplified Technical English style (short active sentences, simple tenses, one instruction per sentence) and keeps every fact and hedge. Use this skill when text must have one reading for a model, program, translator, or non-native reader, such as tool descriptions, error messages, prompts, agent instructions, status reports, or READMEs, or when the user asks to disambiguate, simplify, or apply STE or plain language, even without naming STE. Creative or persuasive copy keeps its own style.
argument-hint: "[text or file]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/ste-lint *)
---

# Rewrite in Simplified Technical English

Rewrite the text so that a reader who cannot ask the author, often a model or a program, has one reading. The rules are the writing rules of ASD-STE100 Issue 9. Its dictionary of approved words is outside this skill, so call the result "STE style". For certified STE, point to the free official copy at https://www.asd-ste100.org/STE_downloads.html.

## Meaning First

- Keep every fact, condition, number, limit, and scope qualifier at its width: "an error after the retries" stays "after the retries", and "retry if needed" stays "if needed".
- Keep every hedge at its strength (may, might, could, can, sometimes, likely). Count the hedges before and after, because a length cap tempts a writer to turn a hedge into a fact. A hedge wins over the tense rule: "may have failed" stays.
- State only what the source states. A cause, count, frequency, mechanism, step, "because", "usually", or "most common" enters only from the source. Reword each claim about its own subject: "without ever leaving the terminal" stays a claim about the terminal.
- Copy code, commands, identifiers, paths, URLs, quoted strings, and names exactly.
- Keep "should" as a recommendation. It becomes an imperative only in an instruction to the agent that acts.

## Modes

Use the mode that the user names, or pick it from the text type.

- **Strict**: procedures, error messages, tool descriptions, prompts, agent instructions, and safety text. Apply all rules. At most 20 words per instruction and 25 per description.
- **Flavored**: READMEs, PR descriptions, changelogs, and explanations. Apply the sentence rules and the 25-word cap in full, and the word rules as advice, because prose needs some range of words.

## Sentence Rules

- One instruction or action per sentence, with at most one condition: "retries up to 3 times before it returns an error" becomes "retries up to 3 times. Then it returns an error."
- Active voice. When the text names the actor, make it the subject: "retries are disabled in the config" becomes "the config disables retries". Use the passive only when the actor is unknown.
- Simple tenses: imperative, infinitive, simple present, past, and future, and a past participle as an adjective. Keep a compound tense that carries a hedge or current relevance ("the job has completed", so its output exists now), and report it with `Kept as-is`.
- One-word verbs for phrasal verbs (Rule 9.3): "take off" becomes "remove", "spin up" becomes "start", and "times out" becomes "reaches its timeout".
- A period for each semicolon (Rule 8.1). Use all other punctuation as usual.
- Noun clusters of 3 words at most.
- Full grammar: keep subjects, verbs, and articles, also when they add length.
- One topic and at most 6 sentences per paragraph. A list for 3 or more steps or conditions.
- Safety text starts with the command or the condition: "Warning: disconnect the power before you open the panel."

## Word Rules

Apply these in Strict mode and suggest them in Flavored mode. Call a replacement word "plainer".

- One term per concept, every time: one of check, verify, and confirm for one action, and one of user, customer, and client for one person.
- Verbs for nouns made from verbs (Rule 3.7): "perform an analysis of" becomes "analyze".
- One part of speech per word: "oil the valve" becomes "apply oil to the valve".
- An -ing form only inside a technical noun ("landing gear"): "when starting the job" becomes "when you start the job".
- The plainest word with one meaning: "follow" becomes "obey", because "follow" can also mean "come after".
- A measurement for each marketing adjective, or remove the adjective with its claim: "blazing-fast" and "fast" both go. Cut the filler around a hedge: "may potentially help to improve" becomes "may improve".
- Keep a necessary technical term, and define it once when it is uncommon English.

## Process

1. Read the whole text for meaning. Pick the mode. Judge each word by its meaning in its context, so "key" in "the key timeout" has one meaning. When every sentence already follows the rules, give the reply for compliant text and stop.
2. Lint each text, also a single sentence, before you rewrite it. Lint a file by its path, or text in a quoted heredoc. Add `--max-words 20` for Strict instructions.

   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/ste-lint README.md
   ${CLAUDE_SKILL_DIR}/scripts/ste-lint --max-words 20 <<'EOF'
   <the text>
   EOF
   ```

   Hard findings break a rule. Judge each advisory finding (`passive-voice`, `present-perfect`), because the rules permit some. The linter checks structure only, so check one instruction per sentence, noun clusters, unlisted phrasal verbs, and meaning by reading, also at zero findings. When the linter cannot run, check all rules by reading, as a silent step.
3. Copy each sentence that follows the rules word for word. Rewrite each sentence that breaks a rule. Keep a longer phrase when a shorter one loses precision.
4. Lint the rewrite. Then compare it with the source for each fact, condition, and hedge.

Stop when each sentence has one reading. Length comes second. When the text states no fact or instruction, say so in one line.

## Output

The caller pastes the reply as it is, so by default the whole reply is the rewritten text. For each longer phrase kept on purpose, add a last line `Kept as-is: <phrase>: <the precision it keeps>`, and write the reason in STE style too. Give notes on removed words or open questions only when the user asks for them. A request to disambiguate, simplify, or apply STE asks for the rewrite alone. In every reply, mention the linter only when the user asks about it, because zero findings proves no compliance.

When the user names a file, edit the file, keep its Markdown structure, and reply with only the `Kept as-is` lines, or `Edited <file>.` when there are none.

When the text already follows the rules, the whole reply is the line `The text already follows the rules.`, and a file stays as it is. The rules fix form only, so questions about the content wait until the user asks.

When the user asks for the reasoning ("show the diff", "which rules", "explain", "before and after"), give this table in place of the text. Then give one line with the reason for each phrase kept longer:

```markdown
| Rule | Original | Rewrite |
| --- | --- | --- |
| Simple tenses | "We have received your request." | "We received your request." |

Mode: Strict. 1 violation.
```

## Examples

<examples>
<example>
<input>An error may have occurred while processing your request due to a possible mismatch in the expected data format, which could be caused by an outdated client version.</input>
<output>An error may have occurred during your request. The cause may be a data format that does not match the expected format. An outdated client version could cause this mismatch.</output>
<why>Three claims in 28 words. Each hedge keeps its strength: "may have occurred" stays, "possible" becomes "may be", and "could be caused by" becomes the active "could cause".</why>
</example>
<example>
<input>Once the upstream job has completed and assuming no errors were raised, the downstream agent should proceed to consume the output artifact, though it is worth noting that partial artifacts are sometimes produced under timeout conditions.</input>
<output>When the upstream job has completed and no errors were raised, the downstream agent should read the output artifact. Partial artifacts sometimes occur under timeout conditions.
Kept as-is: has completed: the output exists when the agent reads it.</output>
<why>A description of what another agent should do, so "should" stays a recommendation and both conditions stay. "Proceed to consume" becomes "read". "Sometimes" stays, and the timeout stays a condition, not a cause.</why>
</example>
</examples>

For a tool description or Flavored prose, first read `references/examples.md`.
