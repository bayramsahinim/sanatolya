"""English narration for "The Number Above Their Head" (Just Needy adaptation).

Each entry: (line_id, spoken_text, subtitle_text). Subtitle text uses digits; the spoken
text is what the narrator reads. Story, order and meaning follow the reference short 1:1.
"""

LINES = [
    ("L01", "One morning, you woke up.", None),
    ("L02", "There was a number above everyone's head.", None),
    ("L03", "Not their age. Not their IQ.", None),
    ("L04", "How many more times you'd see them... in your whole life.", "How many more times you'd see them, in your whole life."),
    ("L05", "You looked in the mirror. Nothing above your own head.", None),
    ("L06", "You went outside. On the subway, everyone had the same number:", None),
    ("L07", "One. You'll never see them again.", "1. You'll never see them again."),
    ("L08", "The baker on the corner: two thousand, one hundred forty.", "The baker on the corner: 2,140."),
    ("L09", "The coworker you never liked: three thousand, nine hundred.", "The coworker you never liked: 3,900."),
    ("L10", "You never chose the people you'd see the most.", None),
    ("L11", "That day, your mom called. \"Coming over Sunday?\" ... \"We'll see,\" you said.", "That day, your mom called. \"Coming over Sunday?\" \"We'll see,\" you said."),
    ("L12", "You went anyway. When she opened the door, it said seventeen.", "You went anyway. When she opened the door, it said 17."),
    ("L13", "You did the math. Two holidays a year, plus her birthday. It was right.", None),
    ("L14", "That evening she said, \"Stay the night.\" ... \"I've got work tomorrow,\" you said.", "That evening she said, \"Stay the night.\" \"I've got work tomorrow,\" you said."),
    ("L15", "When the door closed, the number became sixteen.", "When the door closed, the number became 16."),
    ("L16", "We all think the people we love will always be there.", None),
    ("L17", "So we always leave them for last.", None),
    ("L18", "Your daughter had six thousand, four hundred. But as she grew up, it dropped faster.", "Your daughter had 6,400. But as she grew up, it dropped faster."),
    ("L19", "School. College. Another city.", None),
    ("L20", "In the years she wanted to see you most... you were looking at your phone.", "In the years she wanted to see you most, you were looking at your phone."),
    ("L21", "Then you saw your dad. Above his head: one.", "Then you saw your dad. Above his head: 1."),
    ("L22", "You sat next to him. He talked about the weather, the game, the price of tomatoes.", None),
    ("L23", "You wanted to say something big. You couldn't.", None),
    ("L24", "On your way out, you turned back... Zero.", "On your way out, you turned back... 0."),
    ("L25", "One Sunday night, you couldn't sleep. You opened your contacts and scrolled down.", None),
    ("L26", "Next to every name, a number. You stopped at one.", None),
    ("L27", "Your best friend from school. You never went a day without talking.", None),
    ("L28", "You didn't fight. Nothing happened.", None),
    ("L29", "You just didn't call. Neither did he. Life filled the space.", None),
    ("L30", "He didn't even know you'd lost your dad.", None),
    ("L31", "Next to his name: nine. A few weddings. A few coincidences. That's it.", "Next to his name: 9. A few weddings. A few coincidences. That's it."),
    ("L32", "You typed. Deleted. Then sent: \"Coffee this weekend?\"", None),
    ("L33", "Thirty seconds later, a reply. Like he'd been waiting for years: \"Finally! Yes!\"", "30 seconds later, a reply. Like he'd been waiting for years: \"Finally! Yes!\""),
    ("L34", "When you saw him that weekend, the number wasn't nine anymore. It was one hundred fifty.", "When you saw him that weekend, the number wasn't 9 anymore. It was 150."),
    ("L35", "Those numbers weren't fate. Just a prediction.", None),
    ("L36", "Change what you do, and the number changes too.", None),
    ("L37", "That night, you called your mom. \"I'm coming this Sunday,\" you said. \"And the Sunday after.\"", None),
    ("L38", "You looked in the mirror again. Still nothing above your head.", None),
    ("L39", "Because that number shows how many more times others will see you.", None),
    ("L40", "And you can never see it.", None),
    ("L41", "The first person who comes to mind right now... what number is above their head?", "The first person who comes to mind right now... what number is above their head?"),
    ("L42", "Make it bigger. Today. Then write their name in the comments.", "Make it bigger. Today. Then write their name in the comments."),
]

SPOKEN = {lid: s for lid, s, _ in LINES}
SUB = {lid: (d or s) for lid, s, d in LINES}
IDS = [lid for lid, _, _ in LINES]
