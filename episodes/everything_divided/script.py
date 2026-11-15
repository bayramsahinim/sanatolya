"""Narration for "What If We Divided Everything on Earth?" (English adaptation, ~58 s Short).

Faithful line-by-line translation of the original Turkish narration (see NOTES.md for the
transcript, translation and the small numerical corrections).

Each line: (id, spoken text sent to TTS, caption text shown on screen / in the SRT).
Spoken text spells numbers out so the narrator reads them predictably; captions use digits.
"""

TITLE = "What If We Divided Everything on Earth?"

LINES = [
    # --- 0:00 Earth cake (hook)
    ("hook1", "If we divided everything on Earth equally between eight billion people,",
              "If we divided everything on Earth equally between 8 billion people,"),
    ("hook2", "what do you think you'd get?", "what do you think you'd get?"),
    ("hook3", "Let's split it up!", "Let's split it up!"),
    # --- land
    ("land1", "First, the land.", "First, the land."),
    ("land2", "Divide all the land on Earth, and you'd get about two and a half soccer fields.",
              "Divide all the land on Earth, and you'd get about 2.5 soccer fields."),
    # --- trees
    ("tree1", "Trees?", "Trees?"),
    ("tree2", "There are about three trillion trees on Earth.", "There are about 3 trillion trees on Earth."),
    ("tree3", "So your share is about three hundred seventy-five trees.",
              "So your share is about 375 trees."),
    ("tree4", "Your very own little forest!", "Your very own little forest!"),
    # --- birds
    ("bird1", "There are birds, too:", "There are birds, too:"),
    ("bird2", "six wild birds, and three chickens.", "6 wild birds, and 3 chickens."),
    # --- gold
    ("gold1", "Gold?", "Gold?"),
    ("gold2", "Divide all the gold ever mined, and you'd get about twenty-seven grams.",
              "Divide all the gold ever mined, and you'd get about 27 grams."),
    ("gold3", "That's almost a full ounce!", "That's almost a full ounce!"),
    # --- ants
    ("ant1", "But the real surprise? Ants!", "But the real surprise? Ants!"),
    ("ant2", "There are so many ants on Earth that each of us gets about two and a half million ants.",
             "There are so many ants on Earth that each of us gets about 2.5 million ants."),
    # --- stars
    ("star1", "And the sky!", "And the sky!"),
    ("star2", "Even if we shared out the stars of the Milky Way, at least twelve stars would be yours.",
              "Even if we shared out the stars of the Milky Way, at least 12 stars would be yours."),
    # --- final question
    ("end1", "So, which part of your share would you want most?",
             "So, which part of your share would you want most?"),
    ("end2", "Tell me in the comments!", "Tell me in the comments!"),
    ("end3", "Just imagine: three hundred seventy-five trees, six birds, twelve stars... it's all your share.",
             "Just imagine: 375 trees, 6 birds, 12 stars... it's all your share."),
    ("end4", "Take good care of them!", "Take good care of them!"),
]

# paragraph breaks in the single TTS take (a slightly longer pause after these lines)
PARA_AFTER = {"hook3", "land2", "tree4", "bird2", "gold3", "ant2", "star2", "end2"}

DIRECTOR_NOTES = (
    "Narrator of an educational YouTube Short. Voice: young adult American male, natural and "
    "conversational, confident, curious and slightly playful, clean and bright. Medium-fast pace "
    "with smooth storytelling flow; put natural emphasis on the surprising numbers. Not deep, not a "
    "documentary voice, no exaggerated excitement, never shouting, no long dramatic pauses.\n"
    "Leave a short natural pause between sentences and about half a second between paragraphs.\n"
    "Speak only the transcript below, nothing else.")


def take_text():
    paras, cur = [], []
    for lid, spoken, _ in LINES:
        cur.append(spoken)
        if lid in PARA_AFTER:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return "### DIRECTOR'S NOTES\n" + DIRECTOR_NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(paras)

# On-screen caption groups (1-3 words). "display=spoken" when the caption differs from speech.
CAPTIONS = {
    "hook1": ["If we divided", "everything", "on Earth", "equally between", "8 billion=eight billion", "people,"],
    "hook2": ["what do you", "think you'd get?"],
    "hook3": ["Let's split", "it up!"],
    "land1": ["First,", "the land."],
    "land2": ["Divide all", "the land", "on Earth,", "and you'd get", "about 2.5=about two and a half", "soccer fields."],
    "tree1": ["Trees?"],
    "tree2": ["There are", "about 3 trillion=about three trillion", "trees", "on Earth."],
    "tree3": ["So your share", "is about", "375 trees.=three hundred seventy-five trees"],
    "tree4": ["Your very own", "little forest!"],
    "bird1": ["There are", "birds, too:"],
    "bird2": ["6 wild birds,=six wild birds", "and 3 chickens.=and three chickens"],
    "gold1": ["Gold?"],
    "gold2": ["Divide all", "the gold", "ever mined,", "and you'd get", "about 27 grams.=about twenty-seven grams"],
    "gold3": ["That's almost", "a full ounce!"],
    "ant1": ["But the", "real surprise?", "Ants!"],
    "ant2": ["There are", "so many ants", "on Earth", "that each", "of us gets", "about 2.5=about two and a half", "million ants."],
    "star1": ["And the sky!"],
    "star2": ["Even if", "we shared out", "the stars", "of the Milky Way,", "at least", "12 stars=twelve stars", "would be yours."],
    "end1": ["So, which part", "of your share", "would you", "want most?"],
    "end2": ["Tell me in", "the comments!"],
    "end3": ["Just imagine:", "375 trees,=three hundred seventy-five trees", "6 birds,=six birds", "12 stars...=twelve stars",
             "it's all", "your share."],
    "end4": ["Take good care", "of them!"],
}
