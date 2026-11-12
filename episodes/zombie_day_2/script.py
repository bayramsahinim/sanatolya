"""Just Needy: Zombie Apocalypse, Day 2, "The Cellar". Narration exactly as written by the channel.

Each entry: (line id, speaker, text, delivery note). The narrator is the channel voice
(config/narrator_voice.json); the stranger is a separate, unseen whispering voice.
"""

TITLE = "JUST_NEEDY_ZOMBIE_DAY_2"

LINES = [
    ("n01", "narrator", "Yesterday, the zombies found my farm.", "Matter-of-fact, a little shell-shocked."),
    ("n02", "narrator", "I spent the entire night hiding behind my couch.", "Exhausted, flat."),
    ("n03", "narrator", "Great survival strategy. I know.", "Dry, self-mocking sarcasm."),
    ("n04", "narrator", "At sunrise, someone knocked on the window.", "Slightly tense, curious."),
    ("n05", "narrator", "It was the mailman.", "Deadpan, a beat of disbelief."),
    ("n06", "narrator", "Well... what was LEFT of him.", "Hesitant start, then lean on the word LEFT."),
    ("n07", "narrator", "He was still holding my package.", "Baffled, almost impressed."),
    ("n08", "narrator", "Five stars for commitment.", "Sarcastic, like reviewing a delivery app."),
    ("n09", "narrator", "I grabbed my emergency backpack.", "Quick, confident, a bit proud."),
    ("n10", "narrator", "Two cookies. A phone charger. And one sock.",
     "Listing items with growing doubt; tiny pauses between items, the sock lands flat."),
    ("n11", "narrator", "Perfect. I'm basically a survival expert.", "Fake confidence, obvious sarcasm."),
    ("n12", "narrator", "Outside, more zombies were gathering.", "Tense, lower."),
    ("n13", "narrator", "I needed another way out.", "Urgent but controlled."),
    ("n14", "narrator",
     "Quick survival tip: always plan a second exit. And never enter a space without knowing how you'll escape.",
     "Brisk, clear tip voice, still natural and a little wry."),
    ("n15", "narrator", "Unfortunately, my best idea was the old cellar.", "Resigned, wry."),
    ("n16", "narrator", "I opened the hatch, climbed downstairs, and closed it behind me.", "Quieter, careful, step by step."),
    ("n17", "narrator", "Finally. Quiet.", "Relieved exhale, soft."),
    ("n18", "narrator", "Then I heard someone breathing.", "Hushed, suspenseful, almost a whisper."),
    ("n19", "narrator", "A voice whispered...", "Whispered, slow, suspenseful."),
    ("s01", "stranger", "Turn off that flashlight.", "Urgent whisper, low and tense."),
    ("s02", "stranger", "They're already down here.", "Barely audible whisper, ominous, slow."),
]

TEXT = {lid: t for lid, _, t, _ in LINES}
SPEAKER = {lid: s for lid, s, _, _ in LINES}

STRANGER_VOICE = "Enceladus"
STRANGER_NOTES = ("A mysterious unseen person hiding in a dark cellar during a zombie outbreak. "
                  "Adult, calm but frightened, speaking in a real breathy whisper, close to the listener. "
                  "Not theatrical, not a monster voice.")
