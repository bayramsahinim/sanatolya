"""Narration for "Why Does Coke Taste Better From a Glass Bottle?"

Faithful English translation of the Turkish master reference. Each line carries the
start time (s) of the matching Turkish phrase, so the English voice lands on the same
visual beat as the original.

Turkish source (transcribed) -> English
  0.0  Camdaki kola neden daha lezzetli?
  2.1  Tarif aynı, değişen şişe.
  4.1  Bir şişe kolaya kendi hacminin 4 katı gaz sıkıştırılır.
  6.9  Plastik sağlam görünür,
  9.1  ama bu gaz için bir süzgeçtir.
 11.7  Kabarcıklar duvardan sızar,
 14.0  her hafta %2 kadar.
 16.0  Gazının 6'da birini kaybeden kola, açılmamış olsa bile bayat sayılır.
 19.5  O gaz dilinizde asite dönüşür;
 22.4  sevdiğiniz o yakıcılık budur.
 24.7  Kutu gazı kaçırmaz.
 26.5  Ama içi ince bir plastikle kaplıdır.
 29.0  Bir deneyde bu kaplama, aromaların neredeyse hepsini iki haftada emdi.
 33.0  Cam ise hiçbir şey kaçırmaz, hiçbir şey emmez.
 36.4  Yani camdaki kola daha lezzetli değil...
 39.3  sadece fabrikadan çıktığı gibi.
"""

TITLE = "Why Does Coke Taste Better From a Glass Bottle?"
END = 45.0  # original runtime 45.16 s; closing shot holds after the last line

# (id, turkish_start, english_text, caption chunks)
LINES = [
    ("L01", 0.0, "Why does cola taste better from a glass bottle?",
     ["Why does cola taste better", "from a glass bottle?"]),
    ("L02", 2.1, "The recipe's the same. What changes is the bottle.",
     ["The recipe's the same.", "What changes is the bottle."]),
    ("L03", 4.1, "A bottle of cola has four times its own volume of gas squeezed into it.",
     ["A bottle of cola has", "four times its own volume", "of gas squeezed into it."]),
    ("L04", 6.9, "Plastic looks solid,",
     ["Plastic looks solid,"]),
    ("L05", 9.1, "but to this gas, it's a sieve.",
     ["but to this gas,", "it's a sieve."]),
    ("L06", 11.7, "The bubbles seep through the wall,",
     ["The bubbles seep", "through the wall,"]),
    ("L07", 14.0, "about two percent every week.",
     ["about two percent every week."]),
    ("L08", 16.0, "Cola that's lost a sixth of its gas counts as flat, even if it was never opened.",
     ["Cola that's lost a sixth of its gas", "counts as flat,", "even if it was never opened."]),
    ("L09", 19.5, "That gas turns into acid on your tongue.",
     ["That gas turns into acid", "on your tongue."]),
    ("L10", 22.4, "That's the bite you love.",
     ["That's the bite you love."]),
    ("L11", 24.7, "A can doesn't let the gas out,",
     ["A can doesn't let the gas out,"]),
    ("L12", 26.5, "but the inside is lined with a thin layer of plastic.",
     ["but the inside is lined", "with a thin layer of plastic."]),
    ("L13", 29.0, "In one experiment, this lining absorbed almost all of the aromas in two weeks.",
     ["In one experiment,", "this lining absorbed almost all", "of the aromas in two weeks."]),
    ("L14", 33.0, "Glass, on the other hand, lets nothing out and absorbs nothing.",
     ["Glass, on the other hand,", "lets nothing out and absorbs nothing."]),
    ("L15", 36.4, "So cola in glass doesn't taste better...",
     ["So cola in glass", "doesn't taste better..."]),
    ("L16", 39.3, "it's just exactly how it left the factory.",
     ["it's just exactly", "how it left the factory."]),
]
