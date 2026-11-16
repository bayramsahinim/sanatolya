"""Narration for the English adaptation of the Turkish Kohnstamm short.

Each line: (planned start in seconds, text). Timing follows the source video:
hook 0-4, setup 4-10, 30 s countdown 10-40, release 40-42, reveal 42-48, outro 48-53.
"""

LINES = [
    (0.25, "What if your arms could move... without you telling them to?"),
    (3.95, "Let's try it. Right now."),
    (5.5, "Step into a doorway."),
    (7.1, "Press the backs of your hands outward against the frame. Firmly, but don't force it."),
    (11.95, "And hold it for thirty seconds."),
    (14.5, "A neurologist described this in 1915. It's called the Kohnstamm phenomenon."),
    (19.85, "More than a hundred years later, scientists still don't fully agree on why it happens."),
    (24.6, "Right now, your shoulder muscles are working nonstop against the frame."),
    (28.9, "Hold an effort like that long enough, and even after you stop..."),
    (32.3, "your muscles can keep contracting on their own for a few seconds."),
    (36.6, "Just a little longer..."),
    (40.05, "Now let go. Step out of the doorway..."),
    (42.45, "and let your arms go loose."),
    (44.7, "Are they rising?"),
    (45.8, "That's not you lifting them. That's your nervous system."),
    (48.95, "If nothing happened, don't worry."),
    (50.55, "Responses vary. Some people feel only a little, or nothing at all."),
]

# What the captions/SRT show for spoken numbers etc. (same words, display form)
DISPLAY = {
    "thirty": "30",
}
