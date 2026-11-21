"""English adaptation of the Turkish "baby turns their head away" short.

TR  = original narration (verbatim, from the source video), with its sentence timing in the original
      (measured from the separated source voice stem: speech on/off at -32 dB, pauses >= 0.14 s).
EN  = faithful translation (meaning preserved; only word order adjusted for natural speech).
CAP = on-screen captions: `|` = caption break, *word* = highlighted word (used sparingly, as in the reference).
"""

# id, original start, original end, Turkish, English
LINES = [
    ("s1", 0.16, 4.97, "Bir bebekle oynarken kafasını çeviriyorsa, sakın dikkatini çekmeye çalışma.",
     "If a baby turns their head away while you're playing, don't try to get their attention."),
    ("s2", 5.24, 8.99, "Çoğumuz o an hemen yüzüne gireriz, daha çok ses çıkarırız.",
     "Most of us get right in their face at that moment and make even more noise."),
    ("s3", 9.39, 12.11, "Sıkıldığını ya da ilgisini kaybettiğini sanırız.",
     "We think they're bored, or that they've lost interest."),
    ("s4", 12.41, 13.59, "Ama durum tam tersi.",
     "But it's actually the opposite."),
    ("s5", 13.96, 17.01, "Bebeğin beyni henüz çok az şeyi aynı anda işleyebilir.",
     "A baby's brain can only process a few things at once."),
    ("s6", 17.36, 21.78, "Senin yüzün, sesin, mimiklerin saniyeler içinde onu doldurur.",
     "Your face, your voice, your expressions fill it up within seconds."),
    ("s7a", 22.13, 24.96, "Kafasını çevirmesi \"Senden sıkıldım\" demek değil,",
     "Turning their head doesn't mean \"I'm bored of you.\""),
    ("s7b", 25.35, 28.42, "\"Bir saniye, çok fazla şey oluyor, nefes almam lazım\" demek.",
     "It means \"Hold on, there's too much going on, I need to breathe.\""),
    ("s8", 28.68, 35.49, "O an peşinden gitmez, ona birkaç saniye alan tanırsan kalp atışı yavaşlar, sakinleşir.",
     "If you don't chase them right then, and give them a few seconds of space, their heart rate slows down and they calm down."),
    ("s9", 35.83, 38.41, "Ve birazdan kendi isteğiyle geri döner.",
     "And soon, they'll come back on their own."),
    ("s10", 38.66, 44.26, "Çünkü konuşamayan bir bebeğin \"mola\" demesinin en sessiz yolu gözlerini kaçırmaktır.",
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
