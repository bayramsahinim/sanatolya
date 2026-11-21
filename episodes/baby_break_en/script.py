"""English adaptation of the Turkish "baby turns their head away" short.

TR  = original narration (verbatim, from the source video), with its sentence timing in the original.
EN  = faithful translation (meaning preserved; only word order adjusted for natural speech).
CAP = on-screen captions: `|` = caption break, *word* = highlighted word (used sparingly, as in the reference).
"""

# id, original start, original end, Turkish, English
LINES = [
    ("s1", 0.00, 4.60, "Bir bebekle oynarken kafasını çeviriyorsa, sakın dikkatini çekmeye çalışma.",
     "If a baby turns their head away while you're playing, don't try to get their attention."),
    ("s2", 5.30, 9.30, "Çoğumuz o an hemen yüzüne gireriz, daha çok ses çıkarırız.",
     "Most of us get right in their face at that moment and make even more noise."),
    ("s3", 9.50, 12.30, "Sıkıldığını ya da ilgisini kaybettiğini sanırız.",
     "We think they're bored, or that they've lost interest."),
    ("s4", 12.50, 13.90, "Ama durum tam tersi.",
     "But it's actually the opposite."),
    ("s5", 14.10, 17.40, "Bebeğin beyni henüz çok az şeyi aynı anda işleyebilir.",
     "A baby's brain can only process a few things at once."),
    ("s6", 17.50, 21.60, "Senin yüzün, sesin, mimiklerin saniyeler içinde onu doldurur.",
     "Your face, your voice, your expressions fill it up within seconds."),
    ("s7a", 22.00, 25.10, "Kafasını çevirmesi \"Senden sıkıldım\" demek değil,",
     "Turning their head doesn't mean \"I'm bored of you.\""),
    ("s7b", 25.40, 29.00, "\"Bir saniye, çok fazla şey oluyor, nefes almam lazım\" demek.",
     "It means \"Hold on, there's too much going on, I need to breathe.\""),
    ("s8", 29.30, 35.70, "O an peşinden gitmez, ona birkaç saniye alan tanırsan kalp atışı yavaşlar, sakinleşir.",
     "If you don't chase them right then, and give them a few seconds of space, their heart rate slows down and they calm down."),
    ("s9", 36.00, 38.80, "Ve birazdan kendi isteğiyle geri döner.",
     "And soon, they'll come back on their own."),
    ("s10", 39.00, 44.70, "Çünkü konuşamayan bir bebeğin \"mola\" demesinin en sessiz yolu gözlerini kaçırmaktır.",
     "Because for a baby who can't talk yet, the quietest way to say \"break\" is to look away."),
]

TEXT = {l[0]: l[4] for l in LINES}

CAP = {
    "s1": "If a baby|turns their head|away while|you're playing,|*don't* try to get|their attention.",
    "s2": "Most of us|get right|in their face|at that moment|and make even|more noise.",
    "s3": "We think|they're bored,|or that they've|lost interest.",
    "s4": "But it's actually|the *opposite.*",
    "s5": "A baby's brain|can only process|a few things|at once.",
    "s6": "Your face,|your voice,|your expressions|fill it up|within seconds.",
    "s7a": "Turning their head|doesn't mean|\"I'm bored of you.\"",
    "s7b": "It means|\"Hold on,|there's too much|going on,|I need to *breathe.*\"",
    "s8": "If you don't|chase them|right then,|and give them|a few seconds|of space,|their heart rate|slows down|and they calm down.",
    "s9": "And soon,|they'll come back|on their own.",
    "s10": "Because for a baby|who can't talk yet,|the quietest way|to say \"*break*\"|is to look away.",
}

ORIG_DURATION = 45.53
