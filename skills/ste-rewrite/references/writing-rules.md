# ASD-STE100 Writing Rules: Summary and Sources

This file gives the public description of ASD-STE100 Simplified Technical English. It paraphrases the rule categories. It does not copy the text of the standard or its dictionary of approximately 900 words. For the official document, request the free download at the official site. This file is in STE style, because the skill applies its own rules to itself.

## What ASD-STE100 Is

ASD-STE100 is a controlled natural language. The first release was in 1986, as AECMA Document PSC-85-16598. The publisher is now ASD, the AeroSpace and Defense Industries Association of Europe.

European airlines asked for the standard. Most of their staff were non-native speakers of English. They needed maintenance documents that a reader cannot misread, because a misread instruction on an aircraft can kill people.

The Simplified Technical English Maintenance Group (STEMG) maintains the standard. The download is free since Issue 6 in 2013. The current edition is Issue 9, from January 2025.

## Structure

- **53 writing rules in 9 sections.** They cover word choice, grammar, sentence structure, and style.
- **A dictionary of approximately 900 approved words.** Each word has one meaning and one part of speech. The dictionary also lists approximately 1,200 words to avoid, each with a suggested replacement.
- **A terminology allowance.** An organization can approve its own technical nouns and verbs in addition to the base words. The base dictionary cannot cover the words of each domain.

## Rule Categories

### Word Choice

- Use an approved word only in its approved meaning and part of speech.
- Each word has one meaning. Do not make the reader select a meaning from the context.
- Select the plainer, shorter, more common word in place of a formal or rare synonym.
- Use an approved verb for an action, not a noun made from that verb (Rule 3.7).
- Do not make a phrasal verb from a verb and a preposition (Rule 9.3). The parts do not give the meaning, and both non-native readers and translation software read them incorrectly.

### Verb Forms

- The standard permits these forms: the infinitive, the imperative, the simple present, the simple past, the simple future, and the past participle as an adjective.
- No present perfect, no past perfect, and no other compound tense. The standard forbids "We have received" and permits "We received".
- Use an "-ing" form only in a technical noun, not as a verb form.

### Voice

- A procedure or an instruction must use the active voice.
- Use the passive voice only in descriptive text, and only when the actor is unknown or is of no interest to the reader.

### Sentence Structure

- One instruction in each sentence.
- At most approximately 20 words in a sentence of a procedure or an instruction. At most approximately 25 words in a sentence of descriptive text.
- Keep each part of the sentence, such as the verb, the subject, and the article. The standard gives a warning: a sentence that loses a part becomes ambiguous.
- A noun cluster has 3 words at most. A noun cluster is a group of nouns that modify the last noun.
- Do not use the semicolon (Rule 8.1). The standard says: "You can use all standard English punctuation marks but not the semicolon (;)." Write separate sentences. The standard permits each other standard mark, also the em dash.

### Paragraph and Document Structure

- One topic in each paragraph.
- At most approximately 6 sentences in a paragraph.
- Put a sequence, a set of conditions, or a long enumeration in a numbered or bulleted list, not in prose.

### Safety Instructions

- A safety instruction starts with the command or the condition. It must not come later in the sentence.

### Before and after Examples

Each pair paraphrases a rule as an illustration. A pair does not quote the standard. Each example is in a code span, because this file lints itself with the skill.

| Rule | Before | After | Reason |
| --- | --- | --- | --- |
| One meaning for each word | `Verify the system.` `Check the connections.` `Confirm receipt.` | One approved term, in each of the three sentences | Three near-synonyms make the reader guess if they name one action. |
| Verb, not noun made from a verb | `Perform an inspection of the filter.` | `Inspect the filter.` | The noun hides the action. The filler verb adds no meaning. |
| No phrasal verb | `Take off the access panel.` | `Remove the access panel.` | `take off` also means "depart" and "deduct". |
| Simple tense only | `We have received the technical reports from HQ.` | `We received the technical reports from HQ.` | The present perfect adds a second reading. The simple past does not. |

## Why This Skill Applies STE to Agent Output

STE removes ambiguity for a reader who cannot ask a question. One such reader is a technician on a tarmac with a manual and no author to call.

A model that reads the output of another model, a tool description, or a system message is in the same position. It has no back channel for a question: "does this passive sentence mean that the caller does X, or the callee?" The rules that protect a mechanic from a misread torque value also protect the next model.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/)
- [ASD-STE100: About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe: Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English: Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe: ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)
- [SKYbrary: Simplified Technical English (STE)](https://skybrary.aero/articles/simplified-technical-english-ste)
