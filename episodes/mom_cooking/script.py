"""Script for "I Complained About Mom's Cooking. Big Mistake." (Just Needy Short)."""

TITLE = "I Complained About Mom's Cooking. Big Mistake."
SLUG = "I_Complained_About_Moms_Cooking"

# Narrator lines (Puck, channel narrator). One TTS take; paragraphs separated by pauses.
NARRATION = [
    ("n1a", "Ever complained about your mom's cooking?"),
    ("n1b", "I did."),
    ("n1c", "Big mistake."),
    ("n2", "Then I found out how people got dinner ten thousand years ago."),
    ("n3a", "No fridge."),
    ("n3b", "No delivery."),
    ("n3c", "Not even a microwave!"),
    ("n4a", "I chased my food,"),
    ("n4b", "got chased BY my food…"),
    ("n4c", "and somehow burned a potato."),
    ("n5", "Then suddenly… I was back home."),
]
# paragraph structure for the TTS transcript (indices into NARRATION)
PARAGRAPHS = [["n1a", "n1b", "n1c"], ["n2"], ["n3a", "n3b", "n3c"], ["n4a", "n4b", "n4c"], ["n5"]]

# Dialogue: (id, speaker, text). "Me" is voiced by the narrator voice.
DIALOGUE = [
    ("d1", "Mom", "So… how's the chicken?"),
    ("d2", "Me", "BEST MEAL OF MY LIFE!"),
    ("d3", "Mom", "It's yesterday's leftovers."),
    ("d4", "Me", "Even better."),
]


def all_texts():
    d = dict(NARRATION)
    d.update({lid: t for lid, _, t in DIALOGUE})
    return d
