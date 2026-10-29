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
wrote "the STE linter" and "Bash was denied" in its note about a refused tool call.

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

Haiku 5.5 kept "the user is prompted" in all three runs of `cc-system-prompt-permissions`, and
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
judge split of 2 to 1 caused the other.

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

A strict rule also separates a defect from noise at a glance. A grader that fails 3 of 3 runs is
deterministic. The matrix found two: `actor-named` on `cc-system-prompt-permissions`, and
`one-instruction-per-sentence` on `invisible-space`. Both belonged to Haiku 5.5, and a one-run matrix hid the cause of each one.
