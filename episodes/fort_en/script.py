"""The Empty Fort — English vertical short in the egg-head style (yumurta engine).

The "empty fort strategy" (Romance of the Three Kingdoms, ch. 95; the older anecdote in Pei Songzhi's notes to the
Sanguozhi, quoting Guo Chong): a strategist caught in a small town with a handful of men while the enemy's whole army
marches in opens the gates, has the roads swept, and sits on the wall playing the zither. The enemy general, who knows
him as a man who never takes risks, reads it as an ambush and retreats. Legend more than documented history.
The hero is never named. Pattern of the reference Shorts: strange move in the hook, panic, the odd orders, the enemy's
reasoning, "You see" mechanism, payoff on the last word.
LINES: (line_id, spoken_text).
"""

TITLE = "How One Song Stopped an Entire Army"

LINES = [
    ("hook",    "To stop an army of a hundred and fifty thousand men, he opened the gates. And played a song."),
    ("problem", "You see, his soldiers are far away. In this little town he has a few thousand men, mostly cooks and old guards. Then a scout runs in: the enemy's entire army is coming, and it's almost here."),
    ("stakes",  "Run? Too slow. Fight? Impossible. His officers start to panic."),
    ("orders",  "So he gives the strangest orders of the war. Take down every flag. Hide every soldier. Open all the gates. And sweep the road, like guests are coming."),
    ("wall",    "Then he climbs the wall, lights some incense, sits down with his zither, and starts to play. Smiling."),
    ("enemy",   "The enemy general rides up and freezes. Open gates. Empty streets. A man playing music. He knows this man. He never takes risks. Never. So this has to be a trap."),
    ("retreat", "And he turns the whole army around and runs."),
    ("why",     "You see, a careful man doesn't bluff. So nobody believed he was bluffing."),
    ("end",     "Behind those walls there was no army. Just cooks. And one very good actor."),
]
TEXT = {k: v for k, v in LINES}
