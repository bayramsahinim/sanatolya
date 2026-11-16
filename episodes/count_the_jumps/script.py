"""Narration for "Can You Count the Jumps?" (Just Needy, 9:16 Short).

Adapted from the reference attention test. Story beats kept: challenge -> silent count ->
answer (21) -> the real test (penguin, sky, swapped turner) -> spotlight explanation ->
the original 1999 gorilla study (clearly separated from our demo) -> "how many tricks?".

Each line is synthesised as its own take so the edit can be timed exactly to it.
"""

LINES = [
    ("hook",     "Count the blue hoodie's jumps. Bet you get it wrong."),
    ("go",       "Go!"),
    ("stop",     "Stop! How many did you count?"),
    ("answer",   "Twenty-one."),
    ("penguin",  "But did you notice the penguin?"),
    ("sky",      "Or the sky turning from purple to orange?"),
    ("swap",     "Or that one of the rope turners got swapped?"),
    ("spot",     "Attention works like a spotlight. Whatever falls outside it can slip right past you."),
    ("name",     "It's called inattentional blindness."),
    ("study",    "In a famous 1999 study, about half the people counting basketball passes missed a person in a gorilla suit."),
    ("ask",      "How many tricks did you catch? Zero to three. Tell me in the comments."),
]
TEXT = dict(LINES)
