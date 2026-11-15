"""Just Needy — "Can You Swallow Four Times?" (English adaptation of the Turkish short).

Source narration (Turkish, transcribed)          ->  English line
  Üst üste 4 kez yutkunabilir misin?             ->  Can you swallow four times in a row?
  (title card: Kolay görünüyor, değil mi?)       ->  Sounds easy, right?
  Deneyelim. Hemen şimdi.                        ->  Let's try it. Right now.
  1 / 2 / 3 / (silent 4th attempt)               ->  One... Two... Three... Four...
  4'üncüde takıldın, değil mi?                   ->  Did you get stuck on the fourth one?
  Çünkü yutkunmak aslında bir refleks.           ->  That's because swallowing is partly a reflex.
  Boğazında yutacak bir şey olunca tetikleniyor. ->  It kicks in when there's something in your throat to swallow.
  Tükürük bitince beynin şunu diyor:             ->  When your saliva runs low, your brain basically goes:
  "Yutacak bir şey yok"                          ->  "There's nothing to swallow."
  ve komutunu reddediyor.                        ->  So that next swallow gets a lot harder.   (accuracy fix)
  Hadi, bir daha dene.                           ->  Go on, try it again.
"""

# id, text, start time (s) on the timeline, caption groups (1-3 words)
LINES = [
    ("hook",   "Can you swallow four times in a row?", 0.10,
     ["Can you", "swallow", "four times", "in a row?"]),
    ("easy",   "Sounds easy, right?", None, ["Sounds easy,", "right?"]),
    ("try",    "Let's try it. Right now.", None, ["Let's try it.", "Right now."]),
    ("c1", "One.", 5.10, None),
    ("c2", "Two.", 6.75, None),
    ("c3", "Three.", 8.40, None),
    ("c4", "Four.", 10.05, None),
    ("stuck",  "Did you get stuck on the fourth one?", 12.35,
     ["Did you", "get stuck", "on the", "fourth one?"]),
    ("reflex", "That's because swallowing is partly a reflex.", None,
     ["That's because", "swallowing", "is partly", "a reflex."]),
    ("kicks",  "It kicks in when there's something in your throat to swallow.", None,
     ["It kicks in", "when there's", "something", "in your throat", "to swallow."]),
    ("saliva", "When your saliva runs low, your brain basically goes:", None,
     ["When your", "saliva", "runs low,", "your brain", "basically goes:"]),
    ("nothing", "\"There's nothing to swallow.\"", None, ["\"There's nothing", "to swallow.\""]),
    ("harder", "So that next swallow gets a lot harder.", None,
     ["So that", "next swallow", "gets a lot", "harder."]),
    ("again",  "Go on, try it again.", 25.30, ["Go on,", "try it", "again."]),
]
GAP = 0.22          # gap between consecutive narration lines when start is None
END = 27.3          # total runtime
