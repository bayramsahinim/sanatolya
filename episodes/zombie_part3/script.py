"""Just Needy — Zombie Apocalypse, Part 3: "Don't Let It Out". Narration script (verbatim)."""

# (id, text) — one TTS take per line so every line can be placed exactly on its shot.
NARRATION = [
    ("n01", "A zombie ran toward my farmhouse."),
    ("n02", "Not to attack me."),
    ("n03", "To hide."),
    ("n04", "Behind it, the cornfield was bending in a straight line."),
    ("n05", "But the trees weren't moving."),
    ("n06", "Then a glass on my table started shaking."),
    ("n07", "Here's what we know: vibrations can travel through soil and into nearby buildings."),
    ("n08", "But shaking alone can't tell you the cause."),
    ("n09", "I checked the tractor."),
    ("n10", "Engine off."),
    ("n11", "Outside, the fence posts rattled one after another."),
    ("n12", "Whatever was moving, it was heading toward the barn."),
    ("n13", "Then I saw it."),
    ("n14", "The old maintenance hatch."),
    ("n15", "Its rusted handle began turning."),
    ("n16", "From underneath."),
    ("n17", "My radio crackled for the first time all morning."),
    ("n18", "A voice whispered..."),
]
RADIO = ("r01", "Don't let it out.")

# Per-episode delivery. Voice identity (Puck, model) comes from config/narrator_voice.json.
NARRATOR_NOTES = (
    "Narrator of a dark survival-thriller animation series, telling his own story in first person. "
    "Voice: young adult American male, natural American accent, clear pronunciation, medium-fast pace, "
    "intelligent and conversational, serious and slightly tense, controlled emotion, quiet suspense. "
    "Not a deep movie-trailer voice, not robotic, no comedy, no sarcasm, never shouting.\n"
    "Speak only the transcript below, nothing else.")
LINE_NOTES = {
    "n03": "Short, quiet, unsettled. A beat of disbelief.",
    "n10": "Flat and quiet, a clipped observation.",
    "n13": "Low, tense, almost a breath.",
    "n16": "Very quiet, slow, fearful.",
    "n18": "Hushed and slow, trailing off into silence.",
}
RADIO_NOTES = (
    "A frightened human voice whispering through a weak emergency radio. Breathy, urgent, quiet, "
    "afraid of being overheard. A real person, not a monster, not dramatic. Whisper the line only.")
