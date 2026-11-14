"""Approved English narration for "Can You Spot the Change?".

Each block is one TTS take; each line inside a block is one sentence that will be
cut out of the take on its natural pause. Caption groups (1-3 words) are given with
'|' separators so captions follow phrasing rather than a fixed word count.
"""

BLOCKS = [
    ("hook", [
        ("h1", "I'm going to | trick | your brain."),
        ("h2", "Right in front | of your eyes."),
    ]),
    ("task", [
        ("t1", "Count | every seagull | you see."),
        ("t2", "Only | the birds."),
        ("t3", "Ready?"),
        ("t4", "Go."),
    ]),
    ("reveal", [
        ("r1", "How many?"),
        ("r2", "Nine?"),
        ("r3", "Now | a different | question."),
        ("r4", "What color | was the ship?"),
    ]),
    ("replay", [
        ("p1", "At first, | it was red."),
        ("p2", "Then, | without | a single cut, | it slowly | turned blue."),
    ]),
    ("science", [
        ("s1", "That's | gradual | change blindness."),
        ("s2", "When your attention | is locked | on one task, | slow changes | elsewhere | can slip | past you."),
    ]),
    ("examples", [
        ("e1", "Think of | a snack bag | getting | slightly smaller, | or changes | in routines | you hardly notice."),
        ("e2", "Your brain | isn't recording | every detail."),
        ("e3", "It prioritizes | what matters | right now."),
    ]),
    ("ending", [
        ("n1", "And if you | spotted | the color?"),
        ("n2", "Nice catch."),
        ("n3", "Watch it | again."),
        ("n4", "How many seconds | did it take you | to notice?"),
    ]),
]

# Per-block performance notes (appended to the channel voice direction).
BLOCK_NOTES = {
    "hook": "Slightly playful and confident, like you're letting the viewer in on a challenge.",
    "task": "Clear instructions, a little playful. Short beat before 'Ready?' and a crisp 'Go.'",
    "reveal": "Curious and teasing. 'Nine?' is a quick check. Then lean in on the new question.",
    "replay": "Revealing the trick, intrigued, natural.",
    "science": "Intelligent and curious, explaining something genuinely cool. Conversational, not lecturing.",
    "examples": "Relatable and thoughtful, medium-fast, conversational.",
    "ending": "Warm and playful. A friendly challenge at the end, not a big announcer finish.",
}


def plain(line):
    return " ".join(p.strip() for p in line.split("|"))


def groups(line):
    return [p.strip() for p in line.split("|") if p.strip()]
