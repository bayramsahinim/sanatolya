"""Shot list, cut to the FINAL narration word timings (assets/audio/tts_eiffel/words.json).

Each shot: (id, start_s, end_s, mode) where mode is
  "seq"   - 3D camera/objects animate: every frame rendered in Cycles
  "plate" - locked-off 3D camera: one high-quality plate, all motion is character/2D animation
"""
FPS = 30
DURATION = 59.90
NFRAMES = int(round(DURATION * FPS))

SHOTS = [
    ("s01_deal",      0.00,  1.75, "seq"),    # envelope slides across the desk
    ("s02_tower",     1.75,  3.10, "seq"),    # hero shot of the tower
    ("s03_problem",   3.10,  5.10, "plate"),  # Lustig in front of the tower
    ("s04_own",       5.10,  6.95, "plate"),  # close-up: he didn't own it
    ("s05_aerial",    6.95,  9.25, "seq"),    # Paris 1925, descend to the street
    ("s06_cafe",      9.25, 11.90, "seq"),    # café terrace, Lustig reads, car passes
    ("s07_headline", 11.90, 13.55, "seq"),    # newspaper headline close-up
    ("s08_idea",     13.55, 14.55, "plate"),  # paper lowers - the idea
    ("s09_forge",    14.55, 16.45, "seq"),    # pen signs forged letter
    ("s10_stamp",    16.45, 17.55, "seq"),    # official stamp
    ("s11_letters",  17.55, 18.55, "seq"),    # letter lands on a dealer's desk
    ("s12_lobby",    18.55, 19.75, "seq"),    # luxury hotel lobby tracking
    ("s13_meeting",  19.75, 20.95, "plate"),  # meeting room: his announcement?
    ("s14_plan",     20.95, 26.65, "seq"),    # tower diagram separates into scrap
    ("s15_quiet",    26.65, 29.85, "plate"),  # keep quiet, dealers examine documents
    ("s16_poisson",  29.85, 31.60, "plate"),  # André Poisson
    ("s17_doubts",   31.60, 34.25, "plate"),  # wants it, has doubts
    ("s18_hint",     34.25, 36.40, "plate"),  # Lustig leans in: a private payment
    ("s19_glance",   36.40, 38.45, "plate"),  # exchange of glances
    ("s20_paid",     38.45, 39.95, "seq"),    # envelope passed across the table
    ("s21_exit",     39.95, 41.45, "plate"),  # Lustig leaves the hotel with briefcase
    ("s22_train",    41.45, 43.10, "seq"),    # train departs Paris
    ("s23_realize",  43.10, 45.65, "plate"),  # Poisson re-reads the agreement
    ("s24_empty",    45.65, 47.00, "seq"),    # empty hotel room
    ("s25_silent",   47.00, 50.40, "plate"),  # embarrassed silence
    ("s26_strange",  50.40, 52.10, "seq"),    # train arrives - he's back
    ("s27_again",    52.10, 55.10, "plate"),  # same trick, new dealers
    ("s28_failed",   55.10, 57.15, "plate"),  # this time he failed
    ("s29_final",    57.15, DURATION, "seq"),  # the tower still stands
]


def shot(sid):
    for s in SHOTS:
        if s[0] == sid:
            return s
    raise KeyError(sid)


def frames(sid):
    _, a, b, _ = shot(sid)
    return int(round(a * FPS)), int(round(b * FPS))


def shot_at_frame(f):
    for s in SHOTS:
        a, b = frames(s[0])
        if a <= f < b:
            return s, f - a, b - a
    s = SHOTS[-1]
    a, b = frames(s[0])
    return s, f - a, b - a
