# Just Needy: "What If We Divided Everything on Earth?" (English adaptation)

Production note for `JUST_NEEDY_EVERYTHING_DIVIDED_ENGLISH.mp4` and `.srt`.
Vertical 9:16, 1080×1920, 30 fps, about 58.2 s (the original runs 58.4 s).

## 1. Original Turkish narration (transcript)

| Time | Turkish | English (faithful) |
|---|---|---|
| 0:00 | Dünyadaki her şeyi 8 milyar insana eşit paylaştırırsak | If we shared everything in the world equally among 8 billion people, |
| 0:04 | sence sana ne düşerdi? Hadi paylaştıralım! | what do you think you'd get? Let's share it out! |
| 0:07 | Önce topraklar. | First, the land. |
| 0:08 | Dünyadaki bütün karaları bölsek sana tam 2,5 futbol sahası düşer. | If we divided all the land, you'd get exactly 2.5 football fields. |
| 0:13 | Ağaçlar mı? | Trees? |
| 0:14 | Dünyada 3 trilyon ağaç var. Yani senin payın 370 ağaç. | There are 3 trillion trees in the world, so your share is 370 trees. |
| 0:18 | Kendi küçük ormanın! | Your own little forest! |
| 0:20 | Kuşlar da var: 6 tane vahşi kuşun ve 3 de tavuğun. | There are birds, too: 6 wild birds and 3 chickens. |
| 0:24 | Altın mı? | Gold? |
| 0:25 | Bugüne kadar çıkarılmış bütün altını bölsek sana 27 gram düşer. | If we divided all the gold ever mined, you'd get 27 grams. |
| 0:28 | Yani yaklaşık 15 çeyrek altın! | That's about 15 "quarter" gold coins! |
| 0:32 | Ama asıl sürpriz: karıncalar! | But the real surprise: ants! |
| 0:34 | Dünyada o kadar çok karınca var ki her birimize 2,5 milyon karınca düşüyor. | There are so many ants that each of us gets 2.5 million. |
| 0:39 | Ve gökyüzü! | And the sky! |
| 0:41 | Samanyolu'ndaki yıldızları bile paylaştırsak en az 12 yıldız senin. | Even if we shared the Milky Way's stars, at least 12 would be yours. |
| 0:45 | Peki sen payından en çok hangisini isterdin? Hemen yorumlara yaz. | So which part of your share would you want most? Write it in the comments. |
| 0:49 | Bir düşünsene: 370 ağaç, 6 kuş, 12 yıldız… Hepsi senin payın. | Just imagine: 370 trees, 6 birds, 12 stars… all your share. |
| 0:54 | Onlara iyi bak! | Take good care of them! |

The English script in `episodes/everything_divided/script.py` follows this line by line: same hook, same
examples, same order, same closing question and sign-off. Nothing was added or removed.

## 2. Numerical verification (one denominator throughout: 8 billion people)

| Item | Estimate used | ÷ 8 billion | On screen / narrated |
|---|---|---|---|
| Land | ~149 million km² of land surface (about 29% of Earth's surface, Antarctica included) | ≈ 18,600 m² ≈ 2.6 FIFA fields of 105×68 m | "about 2.5 soccer fields" (+ "rough math, not all of it is usable land") |
| Trees | ~3 trillion (Crowther et al., *Nature* 2015: 3.04 trillion) | 375 | "about 375 trees" |
| Wild birds | ~50 billion (Callaghan et al., *PNAS* 2021) | ≈ 6.2 | "6 wild birds" |
| Chickens | ~25 billion live chickens (FAO livestock stocks, early 2020s) | ≈ 3.1 | "3 chickens" (kept separate from wild birds) |
| Gold | ~220,000 t mined in all history (World Gold Council above-ground stocks, ~216,000–220,000 t) | ≈ 27.5 g | "about 27 grams"; cube ≈ 22 m per side (220,000 t ÷ 19.3 t/m³ ≈ 11,400 m³) |
| Ants | ~20 quadrillion (Schultheiss et al., *PNAS* 2022) | 2.5 million | "about 2.5 million ants" |
| Milky Way stars | 100–400 billion | ≥ 12.5 | "at least 12 stars" (+ "just a thought experiment, nobody owns a star") |

All figures are rounded and use qualifying language ("about", "at least", "rough estimates").
On-screen labels frame each value as a hypothetical equal split, not something anyone owns.

## 3. Corrections made (kept as small as possible)

1. **Trees: 370 → 375.** The original says "3 trillion trees" and then "370 each", but 3 trillion ÷ 8 billion
   is exactly 375. I kept the 3-trillion total and fixed the share, which removes the inconsistency. The same
   375 appears in the tree scene, the recap and the final "just imagine" line.
2. **Land: "exactly 2.5" → "about 2.5".** The real value is about 2.6 standard fields, so the original
   number stays but is no longer called exact. A small sub-label says it's rough math and not all of it
   is usable land.
3. **"15 çeyrek altın" → "almost a full ounce".** A *çeyrek* is a Turkish quarter gold coin of about
   1.75 g, so 27 g ≈ 15 of them. US viewers won't know the coin, so I localized it to the closest
   familiar unit: 27 g ≈ 0.87 troy ounce. The 27 g figure itself is unchanged.

No other numbers changed.

## 4. Production

* **Narration:** the channel narrator voice (`config/narrator_voice.json`: Gemini TTS, voice "Puck")
  with this Short's director notes: young adult American male, medium-fast, curious, slightly playful,
  no documentary voice. It is an original voice. The reference speaker was not cloned, and "How Mine
  Salting Worked" was used only as a delivery reference.
* **Timing:** one continuous take. Each word was force-aligned (espeak-ng reference plus MFCC DTW,
  constrained by the take's own pauses). Pauses were tightened to fit about 58 s. All animation cues
  and the 1–3-word burned-in captions are timed to those word timestamps.
* **Captions:** narration captions are white Montserrat ExtraBold with a black contour, at lower-middle
  (y ≈ 1475 px). Number labels are yellow and sit in the header band at the top, so captions never cover
  the cake, animals or numbers. The SRT holds phrase-level cues (≤ 2 lines × 42 characters) for CC.
* **Visuals:** all animation is procedural and original (Cairo vector rendering with dimensional
  shading). That covers the Earth-cake with real continent outlines, the knife and slicing, the
  floating island with soccer-field markings, 375 individually grown trees, 6 birds and 3 chickens,
  the gold cube and ingot, the magnifier with walking ants, the Milky Way and the recap. No footage
  or branding from the source video is used.
* **Sound:** procedural SFX (cake slices, field pops, leaf rustle, chirps and clucks, a metal ting,
  glass swoop, ant patter, star twinkles, rewind). The music bed sits under the voice and ducks when
  the narrator speaks. The mix is normalized to −14 LUFS.
* **Ending:** like the original, the video rewinds to the Earth-cake opening frame so it loops.
