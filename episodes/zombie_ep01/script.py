"""Narration for "Just Needy — Zombie Apocalypse", Episode 1: The First Morning (Day 1).

Every line is one sync unit: one SRT cue and one animation cue. The whole narration is read
in a single continuous TTS take (consistent voice + natural comic timing), then split back
into lines with word-level alignment.
"""

SERIES = "Just Needy — Zombie Apocalypse"
TITLE = "Zombies On My Farm — Day 1: The First Morning"
SLUG = "Just_Needy_Zombie_Apocalypse_Ep01_The_First_Morning"

# (line id, text as spoken / subtitled)
LINES = [
    # HOOK
    ("l01", "Zombies. On my farm."),
    ("l02", "I woke up to screaming, looked outside, and saw my neighbor chasing the mailman."),
    ("l03", "On all fours."),
    ("l04", "So I did the smartest thing possible."),
    ("l05", "I locked the doors… and made breakfast."),
    # FALSE CONFIDENCE
    ("l06", "I mean, it's a farm. We have food, space, and a well."),
    ("l07", "What could go wrong?"),
    ("l08", "Then the lights died."),
    # SURVIVAL FACT
    ("l09", "And with them, our electric well pump."),
    ("l10", "Fun fact: during a real emergency, clean water becomes a priority fast."),
    ("l11", "A farm doesn't magically make you self-sufficient."),
    # ROOSTER
    ("l12", "Okay. Fine. I'll be quiet and figure this out."),
    ("l13", "That's when our rooster decided it was sunrise. Again."),
    ("l14", "The zombies outside stopped."),
    ("l15", "Slowly turned."),
    ("l16", "Great. My security system has feathers."),
    # SOMETHING IS WRONG
    ("l17", "I ran to shut the window."),
    ("l18", "Then I heard footsteps… inside the house."),
    # CLIFFHANGER
    ("l19", "The back door was open."),
    ("l20", "But I locked that door."),
]

TEXT = dict(LINES)

# Per-paragraph delivery (the take is read paragraph by paragraph, in this order).
PARAGRAPHS = [
    (["l01"], "Immediate and serious, slightly hushed, like you just saw it."),
    (["l02", "l03"], "Fast, incredulous storytelling. Comic pause before 'On all fours.' and say it flatly."),
    (["l04", "l05"], "Dry and sarcastic. Short pause at the ellipsis before 'and made breakfast'."),
    (["l06", "l07"], "Smug, overconfident, relaxed. 'What could go wrong?' is pure naive confidence."),
    (["l08"], "Sudden drop in energy. Flat and serious."),
    (["l09"], "Dawning realization, a little deflated."),
    (["l10", "l11"], "Curious and genuinely informative, quick and light, not a lecture."),
    (["l12"], "Muttering to yourself, calm, a bit annoyed, quieter."),
    (["l13"], "Dry disbelief. Comic pause before 'Again.'"),
    (["l14", "l15"], "Tense, slow, quieter. Leave a beat between the two lines."),
    (["l16"], "Deadpan sarcasm. This is the punchline. Do not oversell it."),
    (["l17"], "Urgent and quick."),
    (["l18"], "Quieter and tense, almost a whisper by 'inside the house'."),
    (["l19"], "Quiet, slow, uneasy."),
    (["l20"], "Very quiet, frightened, slow. The final line of the episode. Say it word for word: 'But I locked that door.' (I locked, not I'd locked)."),
]
