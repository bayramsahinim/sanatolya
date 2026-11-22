"""English adaptation script: "What if every human is related?"

Each line: (line_id, spoken_text, caption_text).
In caption_text, *word* = yellow highlight box, | = forced caption break.
Lines are grouped into TTS takes (one Gemini request per take); the take is
split back into lines with cinecode.align.
"""

LINES = [
    # ---- Hook: Earth
    # one recorded sentence ("What if every person on Earth... was actually your relative?"),
    # split at its natural pause so the captions follow the speech
    ("hook_a", "What if every person on Earth...",
     "What if|*every person*|on Earth..."),
    ("hook_b", "was actually your relative?",
     "was actually|your *relative?*"),
    ("intro", "Let's climb our friend's family tree.",
     "Let's climb our friend's|*family tree.*"),
    # ---- Scene A: your ancestors
    ("par", "He has two parents,",
     "He has|*2 parents,*"),
    ("gp", "four grandparents,",
     "*4 grandparents,*"),
    ("ggp", "and eight great-grandparents.",
     "and *8* great-grandparents."),
    ("dbl", "Every generation back, the number doubles.",
     "Every generation back,|the number *doubles!*"),
    # ---- Scene B: thirty generations
    ("g30", "Thirty generations back, about eight hundred years ago, his tree has over a billion ancestor slots.",
     "*30 generations* back,|about *800 years* ago,|his tree has over|*a billion* ancestor slots."),
    ("pop", "But back then, the whole world had only about four hundred million people.",
     "But back then,|the whole world had|only about|*400 million* people."),
    # ---- Scene C: overlap
    ("same", "So the same people fill many slots, again and again.",
     "So the *same people*|fill many slots,|*again and again.*"),
    ("mix", "And everyone's family trees start to overlap.",
     "And everyone's family trees|start to *overlap.*"),
    # ---- Scene D: shared ancestry
    ("mrca", "One model suggests everyone alive today may share an ancestor from just a few thousand years ago.",
     "One model suggests|everyone alive today|may share *an ancestor*|from just|*a few thousand years* ago."),
    # ---- Scene E: ancient ancestry
    ("rewind", "Now let's rewind much further.",
     "Now let's rewind|*much further.*"),
    ("gen", "Your family tree includes everyone you descend from. But your DNA comes from only some of them.",
     "Your *family tree* includes|everyone you descend from.|But your *DNA* comes|from only *some* of them."),
    # ---- Scene F: mtEve / Y-Adam
    ("mt", "DNA passed from mother to child traces back to one woman in Africa, roughly one hundred fifty to two hundred thousand years ago.",
     "DNA passed from|*mother to child*|traces back to|*one woman* in Africa,|roughly *150,000–200,000*|years ago."),
    ("eve", "Scientists call her Mitochondrial Eve.",
     "Scientists call her|*Mitochondrial Eve.*"),
    ("adam", "DNA passed from father to son traces men back to one man: Y-chromosomal Adam.",
     "DNA passed from|*father to son*|traces men back to one man:|*Y-chromosomal Adam.*"),
    ("couple", "They weren't a couple, and probably didn't even live at the same time.",
     "They *weren't a couple,*|and probably didn't even|live at *the same time.*"),
    ("trace", "Scientists can trace certain genetic lineages back to common ancestors. But these weren't the only people alive at the time.",
     "Scientists can trace|certain *genetic lineages*|back to common ancestors.|But these weren't|*the only people*|alive at the time."),
    ("unbroken", "Their lines are simply the ones that never broke.",
     "Their lines are simply|the ones that|*never broke.*"),
    # ---- Scene G: migration
    ("out", "Later, people moved out of Africa and spread across the globe,",
     "Later, people moved|*out of Africa*|and spread across|*the globe,*"),
    ("route", "into Asia, Europe, Australia, and the Americas.",
     "into *Asia, Europe,*|*Australia,*|and *the Americas.*"),
    # ---- Scene H: final reveal
    ("think", "Just think about it.",
     "*Just think about it.*"),
    ("rel", "Everyone watching this, in Japan, Brazil, or Turkey, is your distant relative.",
     "Everyone watching this,|in *Japan,*|*Brazil,*|or *Turkey,*|is your *distant relative.*"),
    ("end", "Eight billion people. Billions of family stories. And a past that's far more connected than you think.",
     "*8 billion* people.|Billions of|*family stories.*|And a past that's|*far more connected*|than you think."),
]

# lines per TTS take
TAKES = [
    ["hook_a", "hook_b", "intro", "par", "gp", "ggp", "dbl", "g30", "pop"],
    ["same", "mix", "mrca", "rewind", "gen", "mt", "eve"],
    ["adam", "couple", "trace", "unbroken", "out", "route", "think", "rel", "end"],
]

# extra silence (s) after a line, beyond the default gap
GAP_AFTER = {
    "hook_b": 0.25, "intro": 0.1, "dbl": 0.12, "mrca": 0.25, "gen": 0.1, "eve": 0.1, "couple": 0.1,
    "unbroken": 0.2, "route": 0.25, "rel": 0.25,
}
DEFAULT_GAP = 0.07
LEAD_IN = 0.3
TAIL = 2.2

TEXT = {i: s for i, s, _ in LINES}
CAPTION = {i: c for i, _, c in LINES}
