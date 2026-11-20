"""Just Needy Short — "The Stroop Effect Challenge" (English adaptation).

Scene order, challenge words/ink colours and pacing follow the Turkish reference
short (90.8 s): rule demo -> 1935 -> three levels (5 / 6 / 8 cards) -> explainers
between levels -> level 3 read aloud by the narrator -> "? / 19" score card.
"""

# Ink colours: chosen for maximum hue separation on the cream card (#F1EBDD).
INK = {
    "RED":    "#E5352B",
    "BLUE":   "#1E5EE6",
    "GREEN":  "#13873A",
    "BROWN":  "#8A4B14",
    "PURPLE": "#9440D8",
    "YELLOW": "#F2B705",
}

# (word shown, ink colour = correct answer). Mirrors the reference exactly:
# level 1 has two congruent cards on purpose ("two of them matched").
LEVELS = [
    {"name": "LEVEL 1", "label": "EASY", "per_card": 1.60, "cards": [
        ("BLUE", "BLUE"), ("RED", "GREEN"), ("BROWN", "BROWN"), ("GREEN", "PURPLE"), ("PURPLE", "RED")]},
    {"name": "LEVEL 2", "label": "HARDER", "per_card": 1.10, "cards": [
        ("GREEN", "RED"), ("RED", "BLUE"), ("PURPLE", "BROWN"), ("BLUE", "GREEN"), ("BROWN", "PURPLE"),
        ("RED", "BROWN")]},
    {"name": "LEVEL 3", "label": "FINAL", "per_card": 0.95, "cards": [
        ("RED", "BLUE"), ("GREEN", "RED"), ("BROWN", "GREEN"), ("BLUE", "BROWN"), ("PURPLE", "BLUE"),
        ("RED", "PURPLE"), ("BLUE", "RED"), ("GREEN", "BLUE")]},
]
TOTAL = sum(len(l["cards"]) for l in LEVELS)  # 19

# Narration. `at` = earliest start (s); a line never starts before the previous one ends.
LINES = [
    ("hook",    0.25, "Your brain can't stop reading. Let me prove it."),
    ("rule",    None, "Don't read the word. Say the color of the letters."),
    ("demo",    None, "This says red... but the letters are green. So you say: green."),
    ("easy",    None, "Sounds easy."),
    ("y1935",   None, "People have been failing this test since 1935."),
    ("levels",  None, "Three levels. Each one faster than the last."),
    ("bar",     None, "Say every color out loud, before the bar runs out."),
    ("go1",     None, "Level one. Go!"),
    # ---- level 1 cards
    ("matched", "L1_END", "Easy, right? That's because two of them matched."),
    ("trap",    None, "Here's the trap: you can't stop reading."),
    ("lvl2",    None, "Level two. Faster."),
    ("go2",     None, "None of them match. Go!"),
    # ---- level 2 cards
    ("pause",   "L2_END", "Did you feel that tiny pause before every color?"),
    ("auto",    None, "Reading is automatic. Naming a color isn't."),
    ("first",   None, "So reading always gets there first."),
    ("slow",    None, "In 1935, people were almost twice as slow when the word lied."),
    ("canread", None, "And it only works because you can read."),
    ("kids",    None, "Little kids who can't read yet? They don't fall for it."),
    ("lvl3",    None, "Final level. The fastest."),
    ("readyou", None, "And this time... I'll read the words to you. Go!"),
    # ---- level 3 cards (narrator reads the WORDS as a distraction, like the reference)
    ("stop",    "L3_END", "Stop!"),
    ("howmany", None, "How many did you get right? Be honest."),
    ("comment", None, "Drop your score in the comments!"),
    ("believe", None, "Nineteen out of nineteen? I don't believe you."),
]

# Level-3 distractor read-out: the narrator says each printed WORD, one per card.
# Recorded as one take and split on the pauses (see episode.l3_words).
L3_READ = "... ".join(w.capitalize() for w, _ in LEVELS[2]["cards"]) + "."

DIRECTION = (
    "This is a fast, interactive YouTube Short: a color-reading challenge the viewer plays along with. "
    "Tone: curious, playful, lightly competitive, conversational - like daring a friend. Crisp and clear. "
    "Short line, so keep it tight with no long pauses."
)
L3_DIRECTION = (
    "Read exactly these eight color words, in this exact order, as a distraction in a game. "
    "Calm and confident, one word at a time with a clear half-second pause after each word. "
    "Do not add, skip or change any word. Say nothing else."
)
