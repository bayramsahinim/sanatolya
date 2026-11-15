"""Just Needy — Japan's Vanishing People (65 s vertical short).

Faithful English adaptation of the Turkish source short. Turkish transcript (source):
  Japonya'da para verip tek gecede ortadan kaybolabilirsin.
  Bu işi yapan firmalara yonige-ya diyorlar, gece taşıyıcıları.
  Diyelim işini kaybettin, borç boğazına dayandı, ailenin yüzüne bakamıyorsun.
  Bir telefon açıyorsun, gece yarısı farlarını söndürmüş bir kamyonet kapına yanaşıyor.
  Sessizce içeri giren ekip bütün hayatını birkaç kutuya sığdırıyor.
  Hattını da iptal ediyorsun.
  Fiyatı mı? 50 binden 300 bin yene kadar.
  Sabah hiç bilmediğin bir şehirde tek pencereli bir odada uyanıyorsun.
  Annen ertesi gün polise koşuyor.
  Ama Japonya'da kendi isteğiyle giden bir yetişkini ortada suç yoksa polis aramıyor.
  Dosya kapanıyor.
  Annen dedektif tutuyor.
  Kişisel verilere eli değmeyen dedektif de bir yere varamıyor.
  Japonya'da her yıl 80 binden fazla kayıp ihbarı yapılıyor.
  Çoğu bulunuyor.
  Binlercesindense hiç haber çıkmıyor.
  Japonlar bu insanlara jōhatsu diyor, buharlaşanlar.
  Dedektifin annene verdiği raporda tek cümle yazıyor: Oğlunuz gitmeyi seçmiş.

Factual adjustments (minimal):
  * fee: a range; ¥300,000 framed as a bigger/more complex move, not a fixed price
  * police: "usually won't actively search" (not an absolute rule)
  * statistic: 80,486 = ALL missing-person reports received by Japan's National Police
    Agency in 2025 (NPA, "令和7年における行方不明者届受理等の状況"), not a jōhatsu count
  * "thousands never heard from" -> "some", since no verified annual figure exists
"""

LINES = [
    "In Japan, you can pay a company to vanish overnight.",
    "The firms that do it are called yonige-ya. Night movers.",
    "Say you lost your job, the debt is choking you, and you can't face your family.",
    "You make one phone call. At midnight, a van with its headlights off pulls up to your door.",
    "A crew slips in quietly and packs your whole life into a few boxes.",
    "You cancel your phone line, too.",
    "The price? Around fifty thousand yen, and up to three hundred thousand for a complicated move.",
    "By morning, you wake up in a one-window room, in a city you've never seen.",
    "The next day, your mom runs to the police.",
    "But if an adult leaves by choice, and there's no sign of a crime, police in Japan usually won't search.",
    "The file gets closed.",
    "Your mom hires a private detective.",
    "Without access to personal records, he gets nowhere.",
    "In 2025, Japan's police received over eighty thousand missing-person reports, for all kinds of reasons.",
    "Most of them are found.",
    "But some are never heard from again.",
    "The Japanese call people who choose to vanish jōhatsu. The evaporated.",
    "The detective's report to your mom says just one sentence.",
    "Your son chose to leave.",
]

# caption display text overrides (spoken -> shown)
CAPTION_SUBS = {
    "fifty thousand yen": "¥50,000",
    "three hundred thousand": "¥300,000",
    "eighty thousand": "80,000",
}

DIRECTOR = (
    "Narrator of a short mystery-documentary video. Voice: young adult American male, natural "
    "American accent, clear and conversational, curious and intelligent, slightly mysterious, "
    "medium-fast pace like a punchy storytelling short. Not robotic, not overly dramatic, no long "
    "pauses, no booming trailer voice. Keep short natural breaths between sentences. Deliver the "
    "final line quietly and plainly, letting it land.\n"
    "Say \"yonige-ya\" as YOH-nee-geh-yah and \"jōhatsu\" as JOH-hah-tsoo.\n"
    "Speak only the transcript below, nothing else."
)
