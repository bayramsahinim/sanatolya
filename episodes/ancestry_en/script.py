"""English adaptation script: "What if every human is related?"

Each line: (line_id, spoken_text, caption_text).
In caption_text, *word* = yellow highlight box, | = forced caption break.
Lines are grouped into TTS takes (one Gemini request per take); the take is
split back into lines with cinecode.align.
"""

LINES = [
    # ---- Hook: Earth
    ("hook1", "There are over eight billion people on Earth.",
     "There are over|*8 billion*|people on Earth."),
    ("hook2", "But what if we're all related?",
     "But what if|we're *all related?*"),
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
    ("gen", "Your family tree covers everyone you descend from. Your DNA carries pieces from only some of them.",
     "Your *family tree* covers|everyone you descend from.|Your *DNA* carries pieces|from only some of them."),
    # ---- Scene F: mtEve / Y-Adam
    ("mt", "DNA passed from mother to child traces back to one woman in Africa, about one hundred fifty to two hundred thousand years ago.",
     "DNA passed from|*mother to child*|traces back to|*one woman* in Africa,|about *150,000–200,000*|years ago."),
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
    ["hook1", "hook2", "intro", "par", "gp", "ggp", "dbl"],
    ["g30", "pop", "same", "mix", "mrca"],
    ["rewind", "gen", "mt", "eve", "adam", "couple"],
    ["trace", "unbroken", "out", "route"],
    ["think", "rel", "end"],
]

# extra silence (s) after a line, beyond the default gap
GAP_AFTER = {
    "hook2": 0.35, "intro": 0.2, "dbl": 0.25, "pop": 0.15, "mix": 0.15, "mrca": 0.4,
    "rewind": 0.15, "gen": 0.2, "eve": 0.2, "couple": 0.2, "unbroken": 0.3, "route": 0.35,
    "think": 0.1, "rel": 0.35,
}
DEFAULT_GAP = 0.12
LEAD_IN = 0.4
TAIL = 1.8

TEXT = {i: s for i, s, _ in LINES}
CAPTION = {i: c for i, _, c in LINES}
