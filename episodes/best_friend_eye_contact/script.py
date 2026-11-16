"""Faithful English localization of the Turkish reference narration.

Each line: (id, src_start, src_end, turkish, english).
src_start/src_end are the speech boundaries measured in the reference audio
(silence detection, cross-checked against its burned-in captions). The English
take for each line is placed at the same start time so every visual beat lands
exactly where it does in the original.
"""

LINES = [
    ("L01", 0.00, 2.54, "Neden yakın arkadaşınla tek bakışla anlaşırsın?",
     "Why do you and your best friend get each other with just one look?"),
    ("L02", 3.01, 3.96, "Kalabalık bir masa.",
     "A crowded table."),
    ("L03", 4.40, 5.79, "Biri saçma bir şey söyler...",
     "Someone says something ridiculous..."),
    ("L04", 6.05, 8.56, "Ve ikiniz aynı anda göz göze gelirsiniz.",
     "And the two of you lock eyes at the exact same moment."),
    ("L05", 8.98, 9.69, "Tek kelime yok.",
     "Not a single word."),
    ("L06", 10.00, 12.46, "Ama o bir saniyede her şey konuşuldu.",
     "But in that one second, everything got said."),
    ("L07", 13.22, 14.19, "Bu telepati değil.",
     "This isn't telepathy."),
    ("L08", 14.52, 18.60, "Yakın arkadaşların beyni dünyaya şaşırtıcı derecede benzer tepki verir.",
     "Close friends' brains react to the world in surprisingly similar ways."),
    ("L09", 18.94, 20.17, "Aynı şeylere güldünüz,",
     "You've laughed at the same things,"),
    ("L10", 20.43, 21.97, "aynı insanlara sinir oldunuz,",
     "gotten annoyed by the same people,"),
    ("L11", 22.29, 23.72, "ortak bir arşiv kurdunuz.",
     "built a shared archive."),
    ("L12", 24.06, 26.38, "O yüzden kaşındaki minicik bir kalkış...",
     "So the tiniest lift of their eyebrow..."),
    ("L13", 26.59, 29.16, "senin kafanda koca bir zip dosyası gibi açılır.",
     "opens in your head like a giant ZIP file."),
    ("L14", 29.56, 31.25, "Yani o bakış tesadüf değil.",
     "So that look is no coincidence."),
    ("L15", 31.66, 33.98, "O, dünyaya senin gözünle bakan kişi.",
     "That's the person who sees the world through your eyes."),
]

DURATION = 36.0  # reference runs 35.9 s

# Caption phrases (English), split the way the reference reveals its text.
# Each entry: line id -> list of phrases shown one after another.
CAPTION_PHRASES = {
    "L01": ["Why do you and your best friend", "get each other with just one look?"],
    "L02": ["A crowded table."],
    "L03": ["Someone says something ridiculous..."],
    "L04": ["And the two of you", "lock eyes at the exact same moment."],
    "L05": ["Not a single word."],
    "L06": ["But in that one second,", "everything got said."],
    "L07": ["This isn't telepathy."],
    "L08": ["Close friends' brains", "react to the world", "in surprisingly similar ways."],
    "L09": ["You've laughed at the same things,"],
    "L10": ["gotten annoyed by the same people,"],
    "L11": ["built a shared archive."],
    "L12": ["So the tiniest lift", "of their eyebrow..."],
    "L13": ["opens in your head", "like a giant ZIP file."],
    "L14": ["So that look is no coincidence."],
    "L15": ["That's the person who sees", "the world through your eyes."],
}
