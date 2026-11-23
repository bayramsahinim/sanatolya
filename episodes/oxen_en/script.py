"""Fire Oxen — English vertical short in the egg-head style (yumurta engine).

Hannibal at Ager Falernus, 217 BC (Livy 22.16-17, Polybius 3.93-94); the hero is never named.
Pattern of the reference Shorts: strange move in the hook, mockery, rising stakes,
"You see" mechanism, payoff on the last word.
LINES: (line_id, spoken_text).
"""

TITLE = "How 2,000 Cows Beat a Roman Army"

LINES = [
    ("hook",   "He escaped a Roman trap with two thousand cows and a pile of firewood."),
    ("trap",   "You see, his army is boxed into a valley. Mountains on every side, and the only road out is a narrow pass, guarded by four thousand Romans. The Roman general just smiles: \"The fox is in the trap.\""),
    ("stakes", "Every day, the food runs lower. Climb the mountains, and his men get picked off in the dark. Charge the pass, and they die in the bottleneck."),
    ("wood",   "So he orders his men to collect dry branches, and every cow they can find. His officers ask, \"Are we fighting Romans, or having a barbecue?\""),
    ("fire",   "At midnight, they tie the branches to the horns of two thousand cows, set them on fire, and drive them up the mountain."),
    ("guards", "The guards at the pass see thousands of torches climbing the ridge. \"They're escaping over the mountain! After them!\" And they abandon the pass."),
    ("why",    "You see, at night, nobody sees an army. They only see torches. And a torch on a cow looks exactly like a torch in a soldier's hand."),
    ("walk",   "So while the Romans chase the lights, his entire army walks quietly through the empty pass."),
    ("end",    "At dawn, the guards finally catch the army they chased all night: two thousand very confused cows."),
]
TEXT = {k: v for k, v in LINES}
