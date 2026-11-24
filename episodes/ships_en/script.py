"""Ships Over the Hill — English vertical short in the egg-head style (yumurta engine).

Constantinople, April 1453 (Kritovoulos 1.42, Doukas 38, Barbaro's diary, 22 April): the Golden Horn is closed by a
boom chain; the besiegers haul about seventy ships over the hill behind Galata on greased wooden rollers in one night
and launch them inside the harbour. The hero is never named.
Pattern of the reference Shorts: strange move in the hook, mockery, rising stakes,
"You see" mechanism, payoff on the last word.
LINES: (line_id, spoken_text).
"""

TITLE = "How 70 Warships Sailed Over a Hill"

LINES = [
    ("hook",   "To win a battle at sea, he pulled seventy warships out of the sea."),
    ("chain",  "You see, the city's harbor is locked by a giant iron chain. His fleet rams it, and bounces right off. The defenders laugh from the walls: \"Ships can't climb hills.\""),
    ("stakes", "Weeks pass. The walls hold. Supply ships slip into the harbor. And his own generals whisper that it's time to go home."),
    ("road",   "So he orders his men to cut a forest into logs, lay them over the hill behind the harbor, and cover them in grease. His officers whisper, \"Does he think ships can walk?\""),
    ("night",  "In one night, thousands of men drag the ships out of the water, onto the greasy logs, and up the hill. And the sailors sit at their oars, raise the sails, and row through the air, while the drums beat."),
    ("why",    "You see, the chain guards the water. Nobody guards the hill. And on greased logs, a ship slides almost as easily as it floats."),
    ("end",    "At dawn, the defenders look down at their safe harbor and freeze. Seventy enemy ships are floating inside it. And the chain? Still locked."),
]
TEXT = {k: v for k, v in LINES}
