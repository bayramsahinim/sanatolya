"""Faithful English adaptation of the 43 s Turkish short (line order, logic and hook preserved).

Each entry: (key, english line, original-timeline slot start in seconds, original Turkish)."""

LINES = [
    ("hook",     "Why don't you go to sleep when you're dying of exhaustion?", 0.0,
     "Yorgunluktan ölürken neden uyumuyorsun?"),
    ("revenge",  "This isn't insomnia. It's revenge.", 2.5,
     "Uykusuzluk değil bu. İntikam."),
    ("eaten",    "Other people eat up your whole day.", 5.0,
     "Bütün gününü başkaları yiyor."),
    ("list",     "Work, school, traffic, home.", 7.0,
     "İş, okul, trafik, ev."),
    ("yours",    "When night comes, the few hours left belong only to you.", 9.5,
     "Gece olunca geriye kalan o birkaç saat sadece senin."),
    ("brain",    "Your brain doesn't want to let them go. Because if you sleep, tomorrow starts someone else's day all over again.", 13.0,
     "Beynin onları bırakmak istemiyor. Çünkü uyursan yarın yine başkalarının günü başlar."),
    ("battery",  "Plus, at that hour, your willpower is in the red, just like your phone battery. Because you spent all of it during the day.", 18.0,
     "Üstelik o saatte iraden telefonunun pili gibi kırmızıda. Çünkü hepsini gün içinde harcadın."),
    ("steal",    "So you steal hours from your sleep, knowing full well you'll pay for it tomorrow.", 23.5,
     "Bu yüzden uykundan saat çalarsın, yarın ödeyeceğini bile bile."),
    ("loop",     "Sleep less, and the next day your willpower drops even lower. And you do the same thing again.", 27.3,
     "Az uyuyunca ertesi gün iraden daha da azalır. Ve yine aynısını yaparsın."),
    ("ending",   "So it's not that you're not sleepy. You just don't want to give up the only part of the day that's yours.", 32.0,
     "Yani uykun yok değil, günün tek senin olan parçasını vermek istemiyorsun."),
    ("share",    "Send this to the friend who says, \"It's 3 a.m. and I'm still up.\"", 36.3,
     "Bunu gece üçte hâlâ yatmıyorum diyen arkadaşına gönder."),
    ("follow",   "Follow Just Needy to learn how things work.", 39.5,
     "Nasıl çalıştığını öğrenmek için takip et."),
]

VOICE = {
    "model": "gemini-3.8-flash-tts",
    "fallback_models": ["gemini-3.1-flash-tts-preview", "gemini-3.8-flash-lite-tts"],
    "voice": "Puck",
    "notes": ("Narrator of a short explainer video. Voice: young adult American male, natural and "
              "conversational, like telling a friend something interesting. Medium-fast delivery, clear "
              "pronunciation, engaged and confident but never exaggerated, not comedic, not a documentary "
              "voice, no fake excitement. Flowing rhythm with no artificial pauses inside sentences.\n"
              "Leave a clear pause of about one second between paragraphs.\n"
              "Speak only the transcript below, nothing else."),
}
