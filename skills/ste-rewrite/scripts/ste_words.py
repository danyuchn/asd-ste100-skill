"""The word lists of ste-lint. Data only, so that a list grows without a code change.

A list that holds the exact words beats a suffix pattern, because "element"
ends in a nominalization suffix and "seven" ends in a participle suffix.
"""

# A prefix makes a new verb of an irregular stem, and the word boundary of each
# pattern hides the stem inside the longer word: "reset" never matches "set".
# An "un" form stays out, because "unread", "unset", and "undone" are adjectives.
PREFIXED_IRREGULAR = """
misread misled misunderstood mistaken reread rerun rewritten rebuilt resent reset redone
overwritten overtaken overrun overseen overpaid underpaid withheld withdrawn foreseen
""".split()

# Irregular past participles, for the compound tenses.
IRREGULAR = """
given taken made done found seen known shown written built sent set run read kept held left put
cut hit let shut split spread begun become come gone got gotten lost met paid said sold told
thought brought bought caught taught won worn torn born drawn grown thrown flown driven risen
chosen broken spoken frozen hidden ridden forgotten fallen eaten beaten understood stood struck
stuck swung hung led fed bled fled sped bound wound dug spun slid bit lit quit sung sunk drunk
woken sewn sown
""".split() + PREFIXED_IRREGULAR

# A passive sentence uses a transitive participle. "was gone" is an adjective.
INTRANSITIVE = "begun become come gone got gotten fallen risen flown bled fled sped drunk".split()
TRANSITIVE = [word for word in IRREGULAR if word not in INTRANSITIVE]

# Words that end in -ed or -en and are no participle. They would be false hits.
NOT_PARTICIPLE = """
indeed need seed deed speed greed creed breed weed sled hundred sacred embed
seven eleven open often even when then women children dozen citizen garden token
oven linen screen green keen teen between kitten golden wooden sudden siren
listen happen warren heaven maiden pollen burden kindergarten
""".split()

# A passive reading of these is an idiom when "to" comes next.
IDIOM = "supposed used meant".split()

# Nouns made from verbs. The verb says the same in fewer words (Rule 3.7).
NOMINALS = """
analysis analyses review reviews inspection inspections calculation calculations
installation installations modification modifications verification verifications
validation validations evaluation evaluations assessment assessments measurement measurements
adjustment adjustments examination examinations investigation investigations
comparison comparisons conversion conversions configuration configurations
migration migrations deployment deployments replacement replacements removal removals
repair repairs restart restarts backup backups audit audits check checks
search searches query queries update updates upgrade upgrades cleanup cleanups
scan scans diagnosis diagnoses synthesis syntheses
""".split()

# The verbs that carry a nominalization, as in "perform an analysis".
# An entry of more than one word keeps its space, so no list here uses split().
EMPTY_VERBS = ("perform", "performs", "performed", "conduct", "conducts", "conducted",
               "carry out", "carries out", "carried out", "execute", "executes", "executed",
               "do", "does", "did", "make", "makes", "made")

# One adjective may stand between the determiner and the noun.
NOMINAL_ADJECTIVES = "full complete final initial manual quick new detailed thorough second".split()

# Soft phrasal verbs. One plain verb says the same (Rule 9.3).
PHRASAL_VERBS = (r"spin(?:ning|s)? up", r"spun up", r"reach(?:ing|es|ed)? out",
                 r"tim(?:e|es|ing|ed) out",
                 r"div(?:e|es|ing|ed) into", r"dove into", r"kick(?:ing|s|ed)? off",
                 r"circl(?:e|es|ing|ed) back", r"touch(?:ing|es|ed)? base")

# Claims with no measurement.
MARKETING_ADJECTIVES = (r"seamless(?:ly)?", r"robust(?:ly)?", "cutting-edge",
                        r"effortless(?:ly)?", r"blazing[- ]fast", "world-class",
                        "state-of-the-art", r"game-chang(?:ing|er)")

# An adverb or a negation may stand between the auxiliary and the participle.
GAP_WORDS = ("not", "never", "also", "only", "just", "still", "then", "now", "always", "again",
             "already", "ever", "yet", "often", "long", "all", "both", r"\w+ly")
MAX_GAP_WORDS = 2

# Verbs that name one action. error/fault/failure are different things: not here.
SYNONYMS = [
    ("check", "verify", "confirm", "validate"), ("delete", "remove", "erase"),
    ("start", "launch", "begin", "initiate"), ("stop", "halt", "terminate"),
    ("show", "display"), ("use", "utilize", "employ"), ("fix", "repair"),
    ("send", "transmit"), ("get", "retrieve", "fetch", "obtain"),
    ("change", "modify", "alter"),
]

# Forms that no spelling rule gives.
EXTRA_FORMS = {
    "get": ("got", "gotten", "getting"), "send": ("sent",), "show": ("showed", "shown"),
    "begin": ("began", "begun", "beginning"),
}

# A word after one of these is a noun, as in "a sanity check" and "for use".
NOUN_BEFORE = """
a an the this that these those its his her their our your my one two each every
any some no more less for of in at on by with after before during without
sanity health spot spell version error status unit disk
""".split()

# Words that make a pattern. The pattern building lives in ste_rules.
AUXILIARIES = ("is", "are", "was", "were", "been", "being")
PERFECT_AUXILIARIES = ("has", "have", "had")
DETERMINERS = ("a", "an", "the")
MODALS = ("cannot", "may", "might", "could", "should", "would", "must", "can", "will", "shall")

# "is used to run" and "is made for testing" are no passive when a gerund follows.
GERUND_PREPOSITIONS = ("to", "for", "by")

# The endings that build the inflections of a verb.
PLURAL_S = "s"
PLURAL_ES = "es"
PLURAL_IES = "ies"
PAST_ED = "ed"
PAST_D = "d"
PAST_IED = "ied"
GERUND_ING = "ing"
SILENT_E = "e"
CONSONANT_Y = "y"
SIBILANT_ENDINGS = ("s", "x", "z", "ch", "sh")
DOUBLING_CONSONANTS = "pbtdgkmnlr"
VOWELS = "aeiou"

# Markdown alert kinds, as in "[!NOTE]", and the words that end a list item in the wrong place.
ALERT_WORDS = ("note", "tip", "important", "warning", "caution")
LIST_CONJUNCTIONS = ("and", "or")

# An abbreviation ends no sentence.
ABBREVIATIONS = frozenset(("vs.", "cf.", "approx.", "mr.", "mrs.", "ms.", "dr."))
# These end no sentence when a number comes next, as in "No. 5" and "Fig. 2".
NUMBERED = frozenset(("no.", "fig.", "p.", "pp.", "sec.", "vol.", "ch."))
