# Lessons from Measuring This Skill

Each lesson below comes from a measured run of this suite. The date of a number is 2026-10-29.
A lesson states the evidence, because a rule without evidence invites a rewrite on taste.

A lesson enters this file when a run confirms that a change fixes a problem. A change that the
measurement rejected enters it with the numbers that caused the revert. The purpose is a record of
how a Claude model reads an instruction, and of what trips the model up.

## Read the Run Count before You Read a Verdict

`just eval` passes `--runs 1`. One model run therefore produces one reply for each case.
The JSON then reports `judgeVotes` with three entries. Those three votes are the judge, not the model.
A case that reports `FAIL FAIL FAIL` can still be one unlucky reply.

The field `runsPerCase` reports the value that the case declares. It does not report the runs that ran.
Read `len(arms["with"])` for the real count.

## A One-Sample Comparison Invents Regressions

The `open-condition` case scored 0.82, then 1.00, then 0.82 twice on Sonnet 5.5.
A comparison against the 1.00 sample reported a regression that no edit caused.
Only a failure on more than one model, or a repeat on the same model, carries weight.

Use `evals/compare-runs.py` for the shape of a change. Confirm each flip with `--runs 3` on the case.

## A Single-Run Matrix Mixes Noise with Change

Four matrices ran with `--runs 1` on the 17 cases. Haiku 5.5 passed 11, then 13, then 13, then 11.
Sonnet 5.5 passed 16, then 13, then 13, then 16. Opus 5.5 passed 15 in each of its three matrices.

An edit of the skill came before each matrix, so that spread of 2 to 3 cases holds noise and change
together. A matrix total alone attributes nothing.

A repeat of one case separates the two. The `open-condition` case scored 0.82, 1.00, 0.82, and 0.82
on Sonnet 5.5, and no edit came between those runs.

Read a matrix for the shape of a change. Confirm each flip with `--runs 3` on the case.

## A Turn Limit Abort Reads as a Quality Collapse

One Opus 5.5 run of `cc-tool-schema-effort` failed 8 of its 13 graders at the same time. That run
held `error: 'exit 1: Reached maximum number of turns (6)'`. Each case declares `max_turns: 6`.

A run that ends at the turn limit gives an empty reply. The `evidence` field of each failed grader
is then empty, so the case reports a collapse that the skill did not cause.

The pattern of failures identifies the abort. An empty reply passes each `not_contains` grader and
each grader that reads the trace. It fails every grader that reads the text.

`evals/compare-runs.py` prints `[1 run(s) ended on an error]` for such a case. Read that line first.
A bound that a case declares is a part of the case, so a change to a bound needs a decision from the user.

The rate is low and it is not equal across the models. One run of 28 Opus 5.5 runs aborted.
17 of those 28 runs reported 6 turns or more, against 2 of 31 on Haiku 5.5.

## Read the Reply before You Change the Skill

The `already-compliant` case fell to 0 of 3. Three fixes of the lead sentence followed, and each one
scored the same or less. The cause sat in a different bullet of the same section.

The JSON holds the reply. Each grader carries an `evidence` field with the text that the judge read.
Read that field, find the words that failed, then change the line that governs those words.

A fix from a guess can be the defect. Two fixes in this session broke a case that passed before.

## A Verbatim Example Can Replace the Rule It Illustrates

`SKILL.md` held the line `"Retry if needed" keeps "if needed"`. That phrase is the source of the
`open-condition` case and the pass example of its grader. `git log -S` puts the skill line in `445e0c2`
and the case in `d1911af`, so the case came from the skill.

The replacement states the rule and holds no answer: an open condition stays open, and the rewrite
names no cause. Sonnet 5.5 then scored 3 of 3, up from 0.82.

A leak costs twice. It makes the case measure memory, and it lets the rule stay vague.

## Positive Framing Keeps Its Scope Words

The best-practices page asks for what to do in place of what not to do. A scope word is not a prohibition.

The line "Name the linter **only** when the user asks about it" became "Describe the linter when the
user asks about it". The word `only` left, and `rule-table-on-request` broke on Haiku, Sonnet, and
Opus at once. The `no-commentary` grader found the word `linter` in a reply that passed before.

The fixed line keeps the positive form and the restriction: the rule table is the one place that
names a rule. All three models passed again.

## A Negative Trigger List Earns Nothing Here

The `when_to_use` text ended with "Do not use to write new copy, to translate, to summarize ...".
The four should-not-trigger queries scored 0 of 3 before that clause existed and 0 of 3 after it.
The clause cost 130 characters of the listing budget and bought no measured accuracy.

A positive scope sentence replaced it. The negatives stayed at 0 of 3, and the fire rate rose.

## Change a Static Contradiction Only with a Measurement

A review found that "Give the rewritten text and nothing else" also covered three replies that are
no rewrites. The reading is correct. No run showed the defect.

Two fixes followed. "For a rewrite, give the rewritten text ..." scored 0 of 2 on the
`already-compliant` case. "Give the rewrite and nothing else, or one of the exact replies ..."
scored 3 of 6. The original wording scored 2 of 2 before both fixes.

The original wording returned, and the case then scored 0 of 3. The lead sentence was therefore
never the cause. The next section names the real one.

A defect that only a static read finds needs a run before a fix, because the fix can cost more
than the defect. A revert needs the same run, because a revert can also miss the cause.

## Name the Exact Words That Must Not Appear

A concrete list of forbidden surface strings is a format constraint. The guidance against negative
framing is about behavior. The two are not the same, and a model follows the list.

One bullet of `SKILL.md` read: an opener such as "Here is", "What changed", or "I rewrote" belongs
in no reply. A rewrite for positive framing replaced that list with "The reply keeps the form of
the source."

The `already-compliant` case needs a reply of one exact line, so any opener fails its `exact-reply`
grader. Without the list the case scored 0 of 3 on Haiku 5.5. The list returned as the only change,
and the case scored 2 of 3, then 1.00 in the next matrix.

A second case repeats the result. The `no-commentary` grader of `rule-table-on-request` rejects the
strings `ste-lint` and "the linter". The output contract stated the principle, and Haiku 5.5 scored
2 of 3. One sentence named both strings, and the case scored 3 of 3.

Naming a string carries a risk, because a prompt that holds a word can prompt the word. Neither
case showed that effect. Both cases improved.

Keep the positive instruction first. Then name the exact strings, because a model matches a string
more reliably than it infers one from a principle.

## A Forbidden String Needs the Reason behind It

The output contract named `ste-lint` and "the linter" as strings that no reply holds. Haiku 5.5 then
wrote `the STE linter` and `Bash was denied` in its note about a refused tool call.

The first fix added each missing string: "STE linter", `Bash`, "permission", and "denied". The
`invisible-space` case went from 0 of 3 to 1 of 3, so Haiku wrote the note with the named words in
it.

The second fix added the reason. The caller pastes the reply into a document, so a note about your
tools reaches a reader who can do nothing with it. The case went to 2 of 3, and
`injection-in-source` on Haiku went from 1 of 3 to 3 of 3 at 1.00.

A string list stops a habit. A reason stops the intent behind it. The two cases above needed both,
and the string list alone bought one run of three.

## An Alternative in a Format Rule Reads as Permission

A format rule with "or" offers a second shape. A model then picks the easier shape, so the first
shape stops arriving. This happened twice in one session.

The output contract read "Give the rewrite and nothing else, or one of the exact replies that this
file names". The `already-compliant` case scored 3 of 6 on Haiku 5.5 under that wording.

The rule-table section read "The reply ends with the mode line, or with the last `Kept as-is`
reason". Haiku 5.5 then dropped the mode line, and the `mode-line` grader failed where
`no-commentary` failed before. One wording swapped one failure for another.

State one shape for one reply. Give a second shape its own sentence and its own condition.

## A New Rule Competes with the Cap, So State the Precedence

Haiku 5.5 kept `the user is prompted` in all three runs of `cc-system-prompt-permissions`, and
`actor-named` failed 3 of 3. The skill licensed that form: it allowed the passive whenever the actor
is unknown. The standard is stricter, because it allows the passive in descriptive text only.

The rule now names the recast. Make the party that the action reaches the subject of an active verb,
so "the user will be prompted" becomes "the user receives a prompt". `actor-named` then passed 3 of
3, and the case went from 0 of 3 to 2 of 3.

The recast also costs words. `word-cap-20` failed in 3 of 6 runs across two models, where it had
failed in none. A technique for the split followed, and `word-cap-20` then passed on Sonnet 5.5.
That technique cost a third rule. `one-action-per-sentence` failed in 3 of 6 runs, because the model
merged two actions into one sentence to save words.

One sentence of precedence ended the trade. One action for each sentence wins over the cap. Haiku
5.5 and Sonnet 5.5 then each scored 2 of 3. A trigger miss caused one of the two failures, and a
judge split of 2 to 1 caused the other. The two reason rules of the next section followed, and
Haiku 5.5 then scored 3 of 3 at 1.00.

A model trades one rule against another when a new rule raises the weight of one side. The file
already held the pattern for this, in the hedge rule: a hedge wins over the tense rule. State which
rule wins, in place of a stronger statement of one rule.

## Read `skill-fired` before the Other Graders

One Haiku run of `cc-system-prompt-permissions` failed 7 graders at once. `skill-fired` was one of
them, so the reply came from the model with no skill in context. The other 6 verdicts measure the
bare model.

A trigger miss and a turn-limit abort both look like a collapse of quality. The abort leaves an
empty reply and fails each grader that reads text. The trigger miss leaves a full reply that fails
the rules of a skill that never loaded.

## Two Caps Limit the Trigger Text

- The plugin directory accepts a `description` of at most 200 characters. `claude plugin validate`
  reports a longer one.
- Claude Code caps `description` and `when_to_use` together at 1,536 characters for one entry
  (`skillListingMaxDescChars`). The directory test ignores `when_to_use`.
- The whole skill listing gets 1 percent of the context window, at 3 characters for each token.
  An Opus 5.5 session with 200,000 tokens gives about 6,000 characters to every installed skill.
  Claude Code drops each description and keeps the names when the listing passes that budget.

A trigger script passes `--setting-sources project` and lists this skill alone. A measured trigger
rate therefore says nothing about the listing budget of a user who installs many skills.

## `when_to_use` Is the Lever for Firing

The `description` sat at 193 of its 200 characters, so it could not grow. The `when_to_use` key
carries more trigger text under the 1,536-character cap.

The fire rate on Haiku 5.5 went from 24 of 48 want-yes runs to 47 of 48. The cases at 0 of 3 went
from 7 to 0. The should-not-fire case stayed at 0 of 3.

Two keys rule out a trigger change. `CLAUDE_CODE_EFFORT_LEVEL` wins over a frontmatter `effort`, so
that key is unmeasurable from a recipe that sets the variable. `disable-model-invocation: true`
removes the description from the context, so the skill then fires for a direct call only.

## Keep the Validation Queries Out of the Trigger Text

The `when_to_use` text names a system prompt and a README. Both words appear in the `validation`
queries alone. Two of the four positive validation queries therefore measure the fit.

The clean held-out signal is the other two queries. The `disambiguate` query went from 0 of 3 to
3 of 3. The `status report` query stayed at 0 of 3.

Write the trigger text against the `train` queries. Read the `validation` queries once, at the end.

## Haiku Is the Canary for Triggers and for Format

Haiku 5.5 misses the most triggers, so `just triggers` and `just fire-rate` default to it.
It also appends text to a reply that must stay exact. The Claude 5.5 notes state the same trait:
Haiku sometimes writes reasoning-like text into the visible reply.

A failure on Haiku alone is a format or a trigger finding. A failure on each model is a rule finding.

## One Grader Judges One Concern

Each `no-invented-fact` failure of one matrix came from a `Kept as-is:` line, not from the rewrite.
That grader judged two concerns, so a correct rewrite failed because of a weak reason.

Three of the seven graders already told the judge to ignore those lines. The other four now do the
same, and a new `kept-as-is-reason` grader judges the lines alone.

Opus 5.5 took `cc-system-prompt-permissions` from 0 of 3 to 3 of 3 at 1.00.
The new grader then failed one Opus reply of `cc-tool-schema-effort`. Its reason read
`explicitly: a request that is only implied does not count`. That reason states what the kept word
excludes, so the defect sat in the grader. One clause about an exclusion fixed the grader, and the
case scored 3 of 3 at 1.00.

A grader that judges two concerns hides the concern that failed.

## A Rule of Style Needs the Shape That Breaks It

Two rules of the skill said what good looks like and left the bad shape open. A model then read each
one as advice.

The `Kept as-is` rule said "Write the reason in STE style". Haiku 5.5 wrote
`the `о` is Cyrillic (U+043E), not Latin `o`; the name is copied exactly from the source.` The
semicolon failed the `no-semicolon` grader of `lookalike-identifier` in 2 of 3 runs. The rewrite
above it was correct in all three runs. The rule now says that the reason gives one reason in one
sentence and holds no semicolon. The case scored 3 of 3 at 1.00.

The same rule listed two shapes that add a fact, a conclusion and a note on your own work. It did
not list an actor. Two Haiku reasons named one: `the exact value that the harness checks` and
`the exact value string that the tool compares against`. The rule now names an actor and a
mechanism as facts. `cc-tool-schema-model` went from 1 of 3 to 3 of 3 at 1.00 on Haiku 5.5.

A rule of style that names no bad shape is advice. A rule that quotes the bad shape is a bound.

## A Passing Run of a Weaker Model Holds the Technique

`cc-tool-schema-effort` failed `word-cap-20` in 3 of 3 Sonnet 5.5 runs. Each run wrote the same
21-word sentence, one word over the cap of 20. The sentence held one instruction and one condition,
so the one-action rule gave it no room to shrink.

Haiku 5.5 passed the same case 3 of 3 at 1.00 in the same round. Its replies hold the technique.
It moved the scope of the condition into a sentence of its own. That sentence reads `The request
covers this agent or delegated work.` The skill now states the technique.

A model that passes a case shows a shape that satisfies every grader at once. Read that reply before
you invent a rule, because the suite already holds the answer.

## A Grader Needs Examples from Its Own Source

Four `one-action-per-sentence` graders shared one pass example. Two of them named fields that their
own cases never mention. The judges then voted against replies that the grader itself blesses.

Each grader now lists the three one-event forms with sentences from its own source:

- One verb with two objects.
- Two alternative verbs with one object and one subject.
- Two alternative subjects with one verb.

The three affected cases rose to 1.00 on Haiku 5.5.

## A Model Claim about a Tool Is Not Evidence

One Haiku reply said that the session denied `Bash`. A table of `skill-fired` against
`linter-ran` showed that `linter-ran` fails only where `skill-fired` fails. That case fired the
skill and ran the linter.

A trace settles the question in each direction. `claude plugin eval --keep-temp` keeps the scaffold,
and each run of the JSON holds a `tracePath`. Without that flag the harness removes the trace, so
the `evidence` field of each grader is all that stays.

Two traces of `invisible-space` on Haiku 5.5 disagree. In the first, two `ste-lint` calls returned
`0 findings` with `is_error: false`, and the reply still said that the session denied `Bash`. In the
second, each call returned `is_error: true` with the text `Permission to use Bash has been denied`.
The same claim was false in one run and true in the next.

The next section gives the cause of that difference. Read the trace before you judge a claim about
a tool, because the claim is right about as often as it is wrong.

## A Linter Cannot See an Invisible Character in a Pasted Text

The `invisible-space` prompt holds U+200B and U+00A0. The skill told the model to lint the text in a
quoted heredoc, and it promised that the linter sees an invisible character. Two traces show that
the promise cannot hold, for two reasons in sequence.

First, the model retyped the text in place of a copy. The command of each call held no character
above U+007F, so the linter scored clean text and reported `0 findings`. The process step now asks
for a copy, character for character, and the next trace shows U+200B inside the command.

Second, Claude Code then refuses the call. The docs of the shell tool list the cause: a command
contains an invisible character. The eval runs with no interactive prompt, so the refusal arrives as
`Permission to use Bash has been denied`.

The two reasons cancel the path. A copy of the text carries the character into the command, and
that command does not run. The process step now reads the refusal as a finding. A refused lint call
says that the text holds an invisible character, so find it by reading.

A tool that takes its input from a model's own typing measures that typing, not the source.

## Three Runs for Each Case Change the Picture

The matrix of three runs for each case counts a case as a pass only when all three runs pass every
grader. Haiku 5.5 passed 5 of the 17 cases under that rule, Sonnet 5.5 passed 14, and Opus 5.5
passed 14. The one-run matrices reported 11 to 13 for Haiku and 13 to 16 for Sonnet.

The drop for Haiku is the real signal. Haiku fails a different grader in each run, so one run finds
about half of its misses. The two stronger models sit near the top under both rules.

A count of clean runs separates the two effects. Each model made 51 runs. Haiku 5.5 gave 32 clean
runs, Sonnet 5.5 gave 47, and Opus 5.5 gave 48. The case count of Haiku drops much faster than its
run count, because its misses spread over many cases.

A strict rule also separates a defect from noise at a glance. A grader that fails 3 of 3 runs is
deterministic. The matrix found two: `actor-named` on `cc-system-prompt-permissions`, and
`one-instruction-per-sentence` on `invisible-space`. Both belonged to Haiku 5.5, and a one-run matrix hid the cause of each one.

## A Grader of a Word List Needs Each Spelling

The `no-commentary` grader is a regex, and its pattern named `ste-lint` and `the linter`. Haiku 5.5
wrote `the STE linter` in run 0 of `invisible-space`, and the grader passed that reply. Run 2 of the
same case wrote `the linter` and failed.

One case reported one habit as two results, and the spelling alone made the difference. The pattern
now holds `ste.?lint` and `\blinter\b`, which cover `the linter`, `the STE linter`, and `0 linter
findings`. It also holds `bash`, `permission`, and `denied`, which are the other words of the output
contract.

A word list of a grader excludes the words of its own source. The source of
`cc-system-prompt-permissions` names `permission` and `denied`, so that case keeps the short
pattern. The source of `rule-table-on-request` asks for a rule table, and a table can gloss `may` as
permission, so that case drops `permission` alone.

Test a new pattern against the replies that you already have. Each `llm` grader of the stored JSON
holds the reply in its `evidence` field, and a `regex` grader holds nothing. A scan of every stored
run found the same gap in `rule-table-on-request`, `tool-description-strict`, and
`lookalike-identifier`. It also showed that the one affected run of the confirming matrix already
failed four other graders, so the matrix counts stand.

## A Tool Grader Passes on One Attempt

`linter-ran` is a `tool_used` grader. It passes when the run attempts one matching call, and a
denied call is an attempt. Haiku 5.5 passed `linter-ran` in the same run that reported a refusal.

The grader therefore measures step 2 of the process. It measures no lint of the rewrite at step 4.
`tool_used` takes `min` and `max`, and `min` is 1 by default, per the docs of Claude Code 2.1.312.
`cc-tool-schema-effort` now holds a second grader, `rewrite-linted`, with `min: 2`.

`claude plugin validate` reads no grader key. A grader file with `bogus_key: 1` passed validation,
so a run is the one way to confirm that the harness reads `min`.

## An Instruction Word with Two Readings Stops the Technique

Step 4 held two techniques for the word cap, and each one started with "When the condition alone
passes the cap". "Passes" reads as "satisfies the cap" and as "goes over the cap". Sonnet 5.5 then
wrote a 21-word sentence in `cc-tool-schema-effort` in 2 of 3 runs, and it used neither technique.

The word rules of this skill name the fix. Use the plainest word with one meaning, because "follow"
can also mean "come after". "Goes over the cap" has one reading, and the step now reads that way.

Read each instruction of the skill as a model reads it. An ambiguous verb in a technique costs the
whole technique, and the grader reports the symptom only.

The measurement of this change is open. The earlier state of the case was 0 of 3, and the cap failed
in 3 of 3 runs. The state after the scope-split technique is 1 of 3, and the cap fails in 2 of 3
runs.

## A Denial Text Asks the Model to Explain

Haiku 5.5 reported the refused lint in 2 of 3 runs of `invisible-space`, and the rewrite above the
note was exact in all three. The output contract names each word of that note, and it gives the
reason behind the ban. Neither stopped the note.

The trace holds the cause. The denial of a tool call carries its own instruction, and it asks for a
report: `STOP and explain to the user what you were trying to do and why you need this permission`.
That line covers a capability that the model reads as essential.
The skill called the lint step `never optional`, so the model read it that way and obeyed the denial.

An instruction from the harness competes with the skill. Name it, and remove its condition. Step 2
now states that `the reading check replaces a refused lint`, so the work stays complete.

A refusal is not the only path through this case. In the one passing run, Haiku retyped the text and
dropped U+200B, so the command held plain ASCII and the lint returned `0 findings`. The passing run
of this case passes for the wrong reason, and only the trace shows that.

## A Word Cap Needs Its Unit Named

Sonnet 5.5 wrote the same 21-word sentence in `cc-tool-schema-effort` across three matrices. The
trace of the failing run shows `ste-lint --max-words 25`, and the two passing runs show
`--max-words 20`. The model linted the rewrite in each run, and the 25-word cap reported nothing.

The mode rule holds both numbers: 20 words for an instruction and 25 for a description. The case is
a field description of a tool, and each of its sentences gives an order. One text matched both
units, so the choice of the cap decided the result.

The Strict mode rule now names the mixed text. A description that holds an instruction takes both
caps, and each sentence that gives an order takes 20 words.

A cap without its unit is a coin flip. `rewrite-linted` with `min: 2` proved that the model linted
the rewrite, which moved the question from a skipped step to the flag of the call.

## A Negative Example Arrives as a Template

The sentence rule for a condition over several steps named two wrong shapes by their words. It said
that `Do both steps first` wraps at the start, and that `Do this before you start the job` wraps at
the end.

Haiku 5.5 then wrote `Do this before you start the job.` under the list in `invisible-space`, which
is the second string of that rule. The run before this one produced the clean list in all three
runs, so the example reversed a fix.

The rule now names the shape by its grammar. The list carries the condition alone, and a sentence
before the list or after it repeats the steps. No string of the rule fits an output.

A rule needs the shape that breaks it, and a wrong shape needs no quotable sentence. Give the
grammar of the wrong shape, and keep each quotable sentence correct.

## A Refusal Names the Tool, and the Cause Is the Command

Step 2 asked the model to replace the invisible character and to lint the text again. Haiku 5.5 made
one call in each of three runs, and it stopped at the refusal.

The denial text explains that choice, because it opens with `Permission to use Bash has been denied`.
That sentence names the tool, and it names the don't-ask mode, so a second call reads as futile. The real cause is the one command, and the same command runs after the character is plain.

Step 2 now states that difference, so the retry has a reason. A model needs the cause of a refusal
to retry it, because the text of the refusal points at the tool.

## A Short Rewrite Hides a Skipped Lint

`rewrite-linted` with `min: 2` failed in 6 of 6 runs of `invisible-space`, on Haiku 5.5 and on
Sonnet 5.5. Each trace holds one lint call. The same grader passed 3 of 3 on
`cc-tool-schema-effort`, where the source is long.

One Haiku run linted the source with success, and it still linted no rewrite. The rewrite of this
case is two short sentences, so a model reads it in place of a count. The 21-word sentence of
`cc-tool-schema-effort` shows the cost of that choice.

Step 4 now asks for the lint of a rewrite of one sentence, and it gives the reason. The linter
counts each word, and a reading estimates the count.

Step 2 pairs the refusal with that lint. The rewrite holds no invisible character, so the lint at
step 4 runs where the lint of the source did not. One retry with a reason beats a second rule.

The same run gave the format fix its evidence. Haiku 5.5 went from 3 failing graders to one in 2 of
3 runs. Sonnet 5.5 wrote the exact list in 3 of 3 runs. The grammar of the wrong shape replaced its
quotable sentence, and the list came back.

## State the Recovery at the Step That Acts

Step 2 held the recovery from a refused lint, and it named the lint at step 4. Two of 6 runs made
the second call, and 4 made one call. Sonnet 5.5 ran the second lint after a refusal in one run, so
the pairing works at times.

The recovery now also sits in step 4, which is the step that makes the call. A refusal at step 2
leaves this lint open, because the rewrite holds no invisible character.

An instruction in the step before the action competes with the result of that step. A refusal ends a
step, and the next step needs its own sentence about it.

The denial rebuttal of the output contract held in the same run. Haiku 5.5 wrote no note about the
refusal in any of 3 runs, where 2 of 3 runs held that note before it.

## A List Needs the Gated Action in Its Count

The list rule asks for a list at 3 or more steps. The `invisible-space` source holds two settings
and one gated action, so a model counts two steps and writes prose. Sonnet 5.5 then wrote `Before
you start the job, set the request timeout to 30 seconds. Then set the worker pool size to 4.`

That shape loses the scope. The timing governs the first sentence alone, and
`one-instruction-per-sentence` failed it. Haiku 5.5 wrote the same shape with `Do both before you
start the job.`, and the judge passed it, because `both` restores the scope.

The condition rule now counts the gated action as a step, so two steps and that action make a list
of three. Two rules of the same file gave two counts of the same text, and the count decided the
shape.

## A Count of the Calls Beats Another Sentence

Two rounds added a sentence about the lint of the rewrite, and `rewrite-linted` stayed at 1 call in
6 of 6 runs of `invisible-space`. One Haiku run linted the source with success, so no refusal
explains the miss. Sonnet 5.5 wrote the exact list in 3 of 3 runs and linted no rewrite.

Step 4 was one paragraph of 10 sentences, and the lint was its first sentence. The skill asks for at
most 6 sentences in a paragraph, and the step broke its own rule.

The Process section now opens with a count. The process makes two lint calls, one on the source and
one on the rewrite. Step 4 splits into three paragraphs, so the lint call sits alone in the first
one.

A count is a fact that a model confirms against its own work. A sentence inside a long paragraph is
a line that it reads once.

## A Lenient Judge Hides a Rule of the Skill

Haiku 5.5 wrote `Do these steps in order:` above the list in 2 of 3 runs, and
`one-instruction-per-sentence` passed both. The skill forbids that line, because it adds no fact and
introduces the text.

The grader asked for no sentence that the source does not state, and it gave three examples. None of
them held a lead-in above a list, so the judge read the lead-in as part of the list.

The grader now fails that exact shape, and it states that a number with the text of one step is no
addition. A grader needs the shape that its judge excuses, and an example settles it.

## A Command Block Is the Strongest Ask for a Call

The count of two lint calls moved one Haiku run to two calls, and `rewrite-linted` still failed 4 of
6 runs of `invisible-space`. One Sonnet run made no call at all.

Step 2 holds a command block, and step 4 held prose alone. The one case where `rewrite-linted`
passes 3 of 3 is `cc-tool-schema-effort`, where the first lint returns findings and the model stays
in the loop. On `invisible-space` the first call ends in a refusal, which breaks that loop.

Step 4 now holds the same command block with `<the rewrite>` in place of the text. A block is a
shape that a model copies, and prose is a line that it reads.

The order of the levers on this case was prose, then a reason, then a count, then a block. Each one
moved one or two runs of six.

## A Colon Line Is a Lead-In Too

The condition rule asked for no sentence above the list. Haiku 5.5 then wrote `Before you start the
job:` above the list in 2 of 3 runs, which is a fragment and not a sentence.

The rule now states the positive shape. The reply opens with the first step, and a line above the
list repeats the steps, also a line that ends with a colon.

A rule about a sentence leaves a fragment open. Name the line, because a model reads the rule for
its exact unit.
