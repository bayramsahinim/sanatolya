"""Narration for "The Prisoner Who Escaped With Dry Peas" (Just Needy, YouTube Short).

Faithful English translation of the Turkish reference short
"Bu Mahkum Kuru Bezelyeyle Hapisten Kaçtı". One entry per narration line of the source,
in the source's order. `src_t` is where the line starts in the Turkish video (seconds);
the episode places every English line at that same moment so pacing, comic beats and the
ending land where they do in the reference.

Turkish source (transcribed) is kept next to each line for review.
"""

# (line id, source start time, English, Turkish source)
LINES = [
    ("L01", 0.0, "This starving prisoner is feeding his dinner to the wall, and the guards are dying of laughter.",
     "Açlıktan ölen bu mahkum akşam yemeğini duvara yediriyor ve gardiyanlar gülmekten kırılıyor."),
    ("L02", 5.1, "He spoons every single dry pea into a crack.",
     "Her kuru bezelyeyi kaşıkla bir çatlağa dolduruyor."),
    ("L03", 8.5, "He pours his one cup of water in, wishes the wall good night, and pats it.",
     "Tek bardak suyun içine döküyor ve duvara \"İyi geceler\" dileyip okşuyor."),
    ("L04", 12.1, "\"Want some dessert?\" a guard asks,",
     "\"Tatlı ister mi?\" diye soruyor bir gardiyan,"),
    ("L05", 14.6, "waving a huge sausage right under his nose.",
     "burnunun dibinde koca bir sosis sallayarak."),
    ("L06", 17.8, "The prisoner's mouth waters, but he gives his last pea to the wall too.",
     "Mahkumun ağzı sulanıyor ama son bezelyesini de duvara veriyor."),
    ("L07", 20.6, "Then the warden comes to see.",
     "Sonra hapishane müdürü gelip görüyor."),
    ("L08", 22.5, "He laughs until he cries, and gives an order:",
     "Gözünden yaş gelene kadar gülüyor ve emir veriyor:"),
    ("L09", 26.3, "\"Double portions for the wall!\"",
     "\"Duvara çift porsiyon verin!\""),
    ("L10", 27.7, "So the wall eats twice as much.",
     "Böylece duvar iki katı yemek yiyor."),
    ("L11", 29.6, "The prisoner just licks his spoon.",
     "Mahkumsa sadece kaşığı yalıyor."),
    ("L12", 31.5, "\"He's growing a beanstalk!\" a stunned guard says, and the laughter stops.",
     "Bir gardiyan şaşkınlıkla \"Fasulye sırığı yetiştiriyor!\" diyor ve kahkahalar kesiliyor."),
    ("L13", 36.0, "Three weeks and ten thousand peas later, the warden sells tickets to watch the wall sprout.",
     "3 hafta ve 10 bin bezelye sonra müdür duvarın filizlenmesini izlemek için bilet satıyor."),
    ("L14", 41.8, "That evening, a hungry guard steals a handful of peas from the wall and hides them in his water jug.",
     "O akşam aç bir gardiyan duvarın bezelyelerinden bir avuç çalıp su sürahisine saklıyor."),
    ("L15", 46.0, "The prisoner, now just skin and bones, finally speaks:",
     "Derisi kemiğine yapışmış olan mahkum sonunda konuşuyor:"),
    ("L16", 49.4, "\"The wall is thirsty.\"",
     "\"Duvar susadı.\""),
    ("L17", 50.4, "\"Water the beanstalk!\" the warden roars, then grabs a bucket and soaks the crack himself.",
     "Müdür, \"Fasulye sırığını sulayın!\" diye kükrüyor ve bir kova kapıp çatlağı bizzat ıslatıyor."),
    ("L18", 56.0, "That night, the guard's jug of stolen peas explodes with a loud bang.",
     "O gece gardiyanın çalıntı bezelye dolu sürahisi büyük bir gürültüyle patlıyor."),
    ("L19", 60.6, "Then the wall starts to crack.",
     "Ardından duvar çatırdamaya başlıyor."),
    ("L20", 62.8, "Dry peas swell when they get wet.",
     "Kuru bezelyeler ıslanınca şişer."),
    ("L21", 64.9, "Ten thousand peas have already burst the prison wall wide open.",
     "10 bin bezelye hapishane duvarını boydan boya patlattı bile."),
]

SOURCE_DURATION = 68.33

# On-screen gag labels that exist in the source (translated), with source times.
LABELS = [
    # (t0, t1, small header, text)
    (15.3, 17.8, "PRISONER:", "*DOESN'T EVEN FLINCH*"),
    (44.4, 46.0, "", "*WORST STASH EVER*"),
]

# Delivery notes per line (sent to TTS inside the transcript as the narrator's performance cues
# would be audible; kept minimal so the voice stays natural).
TEXT = {lid: en for lid, _, en, _ in LINES}
START = {lid: t for lid, t, _, _ in LINES}
