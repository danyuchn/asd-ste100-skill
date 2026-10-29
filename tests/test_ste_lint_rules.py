"""Rule decisions of ste-lint: which text each rule flags and which it leaves."""
import unittest

from ste_lint_fixture import has, lint, rules


class RuleTests(unittest.TestCase):
    def test_each_rule_fires(self):
        text = ("The panel is removed; spin up the job. "
                "Perform an analysis of the seamless log. We have received the report.")
        got = {f["rule"] for f in lint(text)}
        for rule in ("semicolon", "phrasal-verb", "nominalization", "marketing-adjective",
                     "passive-voice", "present-perfect"):
            self.assertIn(rule, got)
        self.assertTrue(has(" ".join(["word"] * 30) + ".", "long-sentence"))

    def test_levels(self):
        for f in lint("The panel is removed; we have run it."):
            self.assertEqual(f["level"], "advisory" if f["rule"] in
                             ("passive-voice", "present-perfect") else "hard")

    def test_hedges_clean(self):
        self.assertEqual(lint("The request may have failed. It could be a timeout. "
                              "The disk might have filled."), [])

    def test_phrasal_and_marketing_cols(self):
        self.assertEqual(rules("Run `make all` then spin up the node.", "phrasal-verb")[0]["col"], 21)
        self.assertTrue(has("A robust and game-changing tool.", "marketing-adjective"))

    def test_semicolon_positive_and_position(self):
        f = rules("a\nb; c", "semicolon")[0]
        self.assertEqual((f["line"], f["col"]), (2, 2))


class PerfectTests(unittest.TestCase):
    def test_irregular_participles(self):
        self.assertEqual(len(rules("The task has run. We have begun. The job has set the flag.",
                                   "present-perfect")), 3)
        self.assertTrue(has("The job has run.", "present-perfect"))
        self.assertFalse(has("The job may have run.", "present-perfect"))

    def test_modal_protection(self):
        for modal in ("may", "might", "could", "should", "would", "must", "can", "will", "shall"):
            for gap in (" ", "  ", "\t", " not "):
                self.assertFalse(has(f"The task {modal}{gap}have run.", "present-perfect"))
        self.assertFalse(has("The task couldn't have run. The task MAY NOT HAVE RUN.",
                             "present-perfect"))
        self.assertFalse(has("It can’t have run.", "present-perfect"))

    def test_cannot_is_a_modal(self):
        for text in ("It cannot have failed.", "It can't have failed.",
                     "It CANNOT have run."):
            self.assertFalse(has(text, "present-perfect"), text)

    def test_nouns_that_end_in_ed_or_en(self):
        for text in ("They had seven steps.", "The bin had open lids.",
                     "We have need for logs.", "The task had eleven retries.",
                     "The agents have screen output.", "We have even counts."):
            self.assertFalse(has(text, "present-perfect"), text)

    def test_adverb_and_negation_between(self):
        for text in ("We have not run it.", "We have already tested it.",
                     "The job has never started.", "It has been automatically stored.",
                     "The file has not been read."):
            self.assertTrue(has(text, "present-perfect"), text)

    def test_irregular_participle_additions(self):
        for text in ("She has sung it.", "The disk has sunk the write.",
                     "The agent has woken the job."):
            self.assertTrue(has(text, "present-perfect"), text)

    def test_participle_with_a_prefix(self):
        for text in ("The model has misread the note.", "The lead has rewritten the guide.",
                     "The daemon has reset the counter."):
            self.assertTrue(has(text, "present-perfect"), text)


class PassiveTests(unittest.TestCase):
    def test_passive(self):
        self.assertTrue(has("The flag is set.", "passive-voice"))
        self.assertFalse(has("The task is gone.", "passive-voice"))

    def test_adjectives_that_end_in_ed(self):
        for text in ("This is indeed correct.", "The light was red.",
                     "The counts are seven.", "The limit is sacred."):
            self.assertFalse(has(text, "passive-voice"), text)

    def test_idiom_with_to(self):
        for text in ("It is supposed to fail.", "The flag is used to mark a retry.",
                     "The job is meant to stop."):
            self.assertFalse(has(text, "passive-voice"), text)

    def test_adverb_between_and_more_participles(self):
        for text in ("The job is automatically stored.", "The file was sold.",
                     "The flag is not set.", "The panel was never opened.",
                     "The log was understood.", "The lamp is lit."):
            self.assertTrue(has(text, "passive-voice"), text)

    def test_participle_with_a_prefix(self):
        for text in ("The text is misread by a model.", "The guide is rewritten by the lead.",
                     "The counter is reset by the daemon.", "The step is redone.",
                     "The file is overwritten by the job.", "The payment is withheld."):
            self.assertTrue(has(text, "passive-voice"), text)

    def test_un_prefix_stays_an_adjective(self):
        for text in ("The message is unread.", "The work is undone.", "The flag is unset."):
            self.assertFalse(has(text, "passive-voice"), text)


class NominalizationTests(unittest.TestCase):
    def test_positive(self):
        for text in ("We perform the analyses of logs.", "Perform the calculations.",
                     "Do a check of the log.", "Perform a full analysis of the log.",
                     "Make a backup of the disk.", "Carry out the inspection.",
                     "Perform a diagnosis of the unit.", "Carry out the diagnoses.",
                     "Perform a synthesis of the data."):
            self.assertTrue(has(text, "nominalization"), text)

    def test_nouns_with_the_same_ending(self):
        for text in ("Perform the doses at noon.", "Conduct the element test.",
                     "Conduct the thesis review of the paper.", "Make the payment today.",
                     "Perform the experiment."):
            self.assertFalse(has(text, "nominalization"), text)


class SynonymTests(unittest.TestCase):
    def test_positive(self):
        found = rules("Check the config file. Then verify the output. Verify twice.",
                      "synonym-rotation")
        self.assertEqual([(f["line"], f["col"], f["match"]) for f in found], [(1, 29, "verify")])

    def test_negative(self):
        self.assertFalse(has("Check the config. Check the output. Checked twice.",
                             "synonym-rotation"))
        self.assertFalse(has("Delete the file. Show the log.", "synonym-rotation"))

    def test_correct_is_not_rotated(self):
        self.assertFalse(has("Correct the file. Fix the log.", "synonym-rotation"))

    def test_document_order_and_masking(self):
        found = rules("Remove it.\nDelete it.\nErase it.", "synonym-rotation")
        self.assertEqual([f["line"] for f in found], [2, 3])
        self.assertFalse(has("Remove `delete` it.", "synonym-rotation"))

    def test_noun_use_is_not_a_rotation(self):
        for text in ("Do a sanity check. Then verify the output.",
                     "At the start, begin the job.",
                     "The file is fit for use. Utilize the kit.",
                     "The error check runs first. Validate the input."):
            self.assertFalse(has(text, "synonym-rotation"), text)

    def test_inflected_forms_rotate(self):
        for text in ("Deleting the log. Remove the cache.",
                     "Modifies the file. Change it.",
                     "Retrieving the log. Get the file.",
                     "Stopped the job. Halt the agent.",
                     "Launches the task. Start the next one.",
                     "Erased the log. Delete the cache."):
            self.assertTrue(has(text, "synonym-rotation"), text)


if __name__ == "__main__":
    unittest.main()
