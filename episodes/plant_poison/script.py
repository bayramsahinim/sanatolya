"""English adaptation of the Turkish short about tobacco / nicotine.

Each line is anchored to the source caption block it replaces: (src_start, src_end) are the
seconds in the Turkish video where that sentence's caption is on screen.
"""
# (english line, turkish original, src_start, src_end)
LINES = [
    ("A cigarette is actually a drug...", "Sigara... aslında bir ilaç,", 0.00, 2.46),
    ("...but not one made to heal.", "ama iyileştirmek için değil.", 2.46, 5.06),
    ("The tobacco plant can't run. It can't hide.", "Tütün bitkisi kaçamaz, saklanamaz.", 5.06, 8.06),
    ("So instead, it carries a poison in its leaves: nicotine.",
     "Onun yerine yapraklarında bir zehir taşır: nikotin.", 8.06, 11.96),
    ("An insect bites the leaf...", "Bir böcek yaprağı ısırır...", 11.96, 14.00),
    ("...and starts to tremble. Then it can't move at all.",
     "...titremeye başlar. Sonra kıpırdayamaz.", 14.00, 17.29),
    ("Farmers noticed this centuries ago.", "Çiftçiler yüzyıllar önce bunu fark etti.", 17.29, 20.00),
    ("They soaked tobacco leaves in water and sprayed that water on their fields.",
     "Tütün yapraklarını suda bekletip tarlalarına sıktılar.", 20.00, 23.50),
    ("It became one of the world's first insecticides.",
     "Dünyanın ilk böcek ilaçlarından biri oldu.", 23.50, 26.38),
    ("Later, it was banned in many countries,", "Sonra birçok ülkede yasaklandı,", 26.38, 28.38),
    ("because it was too poisonous for humans, too.", "çünkü insanlar için de fazla zehirliydi.", 28.38, 31.33),
    ("Banned in the fields...", "Tarlalarda yasak.", 31.33, 32.96),
    ("...but allowed on our lips.", "Ama dudaklarımızda serbest.", 32.96, 34.73),
    ("The same substance that paralyzes the insect...", "Böceği felç eden o madde,", 34.73, 36.54),
    ("...gives us a brief moment of relief.", "bize kısa bir rahatlama verir.", 36.54, 38.63),
    ("Then you want it again.", "Sonra onu tekrar ister.", 38.63, 40.50),
    ("A plant protected itself with this poison.", "Bir bitki, bu zehirle kendini korudu.", 40.50, 43.25),
    ("We called that poison... a “smoke break.”", "Biz o zehre... “mola” adını verdik.", 43.25, 46.78),
]

# Burned-in caption groups (1-3 words), "|" = cut. Words must match LINES exactly.
CAPS = [
    "A cigarette | is actually | a drug...",
    "...but not one | made to heal.",
    "The tobacco plant | can't run. | It can't hide.",
    "So instead, | it carries | a poison | in its leaves: | nicotine.",
    "An insect | bites the leaf...",
    "...and starts | to tremble. | Then it | can't move | at all.",
    "Farmers | noticed this | centuries ago.",
    "They soaked | tobacco leaves | in water | and sprayed | that water | on their fields.",
    "It became | one of | the world's first | insecticides.",
    "Later, | it was banned | in many countries,",
    "because | it was too | poisonous | for humans, too.",
    "Banned | in the fields...",
    "...but allowed | on our lips.",
    "The same | substance | that paralyzes | the insect...",
    "...gives us | a brief moment | of relief.",
    "Then you | want it again.",
    "A plant | protected itself | with this poison.",
    "We called | that poison... | a “smoke break.”",
]
assert all(c.replace(" | ", " ") == l[0] for c, l in zip(CAPS, LINES)), "CAPS/LINES mismatch"
