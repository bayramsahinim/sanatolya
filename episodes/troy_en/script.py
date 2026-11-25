"""The Trojan Horse — English vertical short (new cast).

LINES: (line_id, spoken_text). Captions are generated word by word from the spoken text.
CAPTION_FIX maps a spoken token to the caption spelling (e.g. TTS respelling of names).
"""

TITLE = "The Trojans Destroyed Their Own Walls"

LINES = [
    ("hook",   "After ten years of war, the Greeks leave their enemy a giant wooden horse, and sail home."),
    ("beach",  "The Trojans rush to the beach. No army. No ships. Just a horse."),
    ("spear",  "A priest named Laocoön hurls a spear into its side, and it sounds... hollow."),
    ("beware", "\"Beware of Greeks bearing gifts!\""),
    ("sinon",  "Then they find one Greek hiding in the reeds, hands tied. His name is Sinon."),
    ("lie",    "Sobbing, he swears: \"It's a gift for Athena. If it enters your city, Troy can never fall. "
               "That's why they built it too big for your gates.\""),
    ("snakes", "Right on cue, two giant sea serpents crawl out of the ocean and strangle Laocoön. "
               "Message received: the horse is sacred."),
    ("walls",  "So how do you get a horse through a gate it doesn't fit? The Trojans tear down their own walls."),
    ("cass",   "Princess Cassandra screams, \"There are soldiers inside!\" Nobody believes her. "
               "She's literally cursed so nobody ever will."),
    ("helen",  "That night, Helen circles the horse, imitating the voices of the soldiers' wives."),
    ("hand",   "One soldier is about to answer, until Odysseus clamps a hand over his mouth."),
    ("night",  "At midnight, Sinon opens the hatch. The soldiers open the gates, "
               "and the fleet that was hiding behind an island sails back."),
    ("end",    "For ten years, the Greeks couldn't break those walls. The Trojans did it themselves, in one afternoon."),
]

TEXT = {k: v for k, v in LINES}

# words that get a yellow caption (lower-case, punctuation stripped)
HIGHLIGHT = {"horse", "hollow", "beware", "gifts", "sinon", "athena", "never", "too", "big", "serpents", "sacred",
             "own", "walls", "nobody", "cursed", "wives", "mouth", "hatch", "gates", "fleet", "ten", "years",
             "themselves", "afternoon", "laocoön", "cassandra", "helen", "odysseus"}
