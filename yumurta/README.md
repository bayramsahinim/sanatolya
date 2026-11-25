# yumurta-stili

**3B bir dünyada 2B yumurta kafalı karakterler. Claude ile, koddan, kare kare.**

Bu repo, 10–35 milyon izlenen "yumurta kafa" animasyonlu hikâye Shorts'larının stilini **ölçerek** yeniden üretir:

- Dünya three.js ile tarayıcıda çiziliyor.
- Karakterler Canvas 2D kartları olarak çiziliyor.
- Kareler Puppeteer ile tek tek yakalanıyor ve ffmpeg ile birleştiriliyor.

Remotion, React, Blender ya da yapay zekâ video üreticisi yok. Sadece Claude (isterseniz Codex ya da Antigravity) ve iki npm paketi.

Örnek: **İs Odası** (`stories/is-odasi/`). Anlatılana göre Mimar Sinan, Süleymaniye'nin kandil isini kapının üstündeki küçük bir odada toplar ve o is mürekkebe dönüşür. 39 sn, 1080×1920, 30 fps. Tam çözünürlükte 1.165 kare yaklaşık 2,5 dakikada render edilir (gölgeler ve ışık halesi dahil).

▶ **Bitmiş video:** [`ornek/is-odasi.mp4`](ornek/is-odasi.mp4) (1080×1920, sesli, 9 MB)

## İçindekiler

| Yol | Ne |
|---|---|
| `SKILL.md` | Claude için skill: baştan sona iş akışı, kurallar, tuzaklar |
| `STIL_KITABI.md` | 10 referans Short'tan ölçülen sayılar: metin, kamera, ışık, karakterin yüz ölçüleri, altyazı; örnek videonun aynı ölçülerle karşılaştırması |
| `analiz/` | Yedi ayrıntılı rapor (ışık, renk, karakter, çizgi, derinlik, hareket, doku): her ölçüm referansta ve örnek videoda, hedef aralıklar ve kurallar. `analiz/veri/` ham ölçüm sonuçlarını (JSON) tutuyor |
| `referans/` | Ölçüm işlenmiş referans kolajları: çizgi kalınlığı, ışık ve hale, renk aileleri, yüz ölçüleri, kamera hareketi; her birinin yanında örnek videodan aynı ölçüyle bir kare |
| `engine/` | Motor: `render.mjs` (kare yakalama), `faces.mjs` (karakter sayfası: bütün karakterler × bütün ifadeler), `src/post.js` (mürekkep + lens bulanıklığı + ışık halesi + renk), `src/toon.js` (karakterler, yüz ifadeleri, gölge kartı ve 3B kol), `src/camera.js` (kamera), `src/vista.js` (pencere manzaraları, delikli duvar), `src/props.js` (3B kandil, çizgili kemer), `src/paint.js` (boyalı dokular: taş, ahşap, halı, çini, kuşak, kubbe), `src/fx.js` (duman, rüzgâr, ışık huzmesi, toz), `src/captions.js`, `audio/mix.py` (sentez müzik + efekt + miks) |
| `tools/` | `kelime_saat.py` (ses → kelime saatleri, metnin yazımıyla), `zarf.py` (dudak senkronu için ses zarfı), `bosluk_kes.py` (seslendirmedeki boşlukları kısaltır, istenirse hızlandırır) |
| `stories/is-odasi/` | Örnek hikâye: `story.js` (setler, oyuncular, kamera; her şey kelimelere bağlı), `voice/words.json`, `SCRIPT.md` |
| `ornek/is-odasi.mp4` | Örnek hikâyenin bitmiş hâli |
| `AGENTS.md` | Codex ve benzeri ajanlar için kısa giriş: önce `SKILL.md` |
| `requirements.txt` | Python paketleri |

## Kurulum

1. Gerekenler: Node 18+, Python 3.10+, ffmpeg, Google Chrome. Chrome başka bir yerdeyse ya da Chromium kullanıyorsanız yolunu `CHROME_PATH` ile verin.
2. Paketleri kurun:
   ```bash
   cd engine && npm install
   pip install -r requirements.txt
   ```
   `torch`, `transformers` ve `librosa` yalnızca kelime saatleri (`tools/kelime_saat.py`) için gerekiyor.
3. **Claude Code:** klasörü `~/.claude/skills/yumurta-stili/` altına kopyalayın. Sonra şunu söyleyin: *"yumurta stiliyle … hakkında bir Shorts yap"*. Metni seslendirip ses dosyasını verdiğinizde sahneleri kelimelere bağlar.
4. **Codex, Antigravity ya da başka bir kod ajanı:** repo klasörünü açın ve şunu söyleyin: *"SKILL.md'yi oku, yumurta stiliyle … hakkında bir Shorts yap"*. Codex, kökteki `AGENTS.md` dosyasını kendiliğinden okur; o dosya da ajanı `SKILL.md`'ye yönlendirir.

## Hızlı kullanım

1. Ses. Örnek hikâyenin sesi repoda (`stories/is-odasi/voice/voice.wav`, Google AI Studio TTS), kelime saatleri ve dudak zarfı da hazır; örneği denemek için 2. adıma geçebilirsiniz. Kendi hikâyenizde (`stories/<ad>/`) sesinizi koyup bu ikisini çıkarın:
   ```bash
   cp ses.wav stories/<ad>/voice/voice.wav
   python tools/kelime_saat.py stories/<ad>/voice/voice.wav stories/<ad>/voice/script.txt stories/<ad>/voice/words.json
   python tools/zarf.py stories/<ad>/voice/voice.wav stories/<ad>/voice/env.json
   ```
   TTS sesi yavaşsa ya da cümle aralarında uzun boşluk varsa, önce boşlukları kısaltıp hızlandırın, sonra kelime saatlerini yeniden çıkarın. Türkçe için hedef saniyede 2,4–2,9 kelime:
   ```bash
   python tools/kelime_saat.py ham.wav stories/<ad>/voice/script.txt ham_kelimeler.json
   python tools/bosluk_kes.py ham.wav ham_kelimeler.json stories/<ad>/voice/voice.wav 1.3
   ```
   Kontrol: `kelime_saat.py` çıktısındaki "heard exactly" satırı, hızlandırılmış seste kelimelerin hâlâ anlaşılıp anlaşılmadığını gösterir.
2. Karakterlere ve ifadelerine tek sayfada bakın, sonra seçilen saniyelerden bir kontrol kolajı alın (yarım çözünürlük):
   ```bash
   cd engine && node faces.mjs is-odasi --zoom
   node render.mjs is-odasi --stills=0.5,6,12,20,30,38 --scale=0.5
   ```
3. Sesi miksleyin ve videoyu render edin:
   ```bash
   node render.mjs is-odasi --cues
   python audio/mix.py ../stories/is-odasi
   node render.mjs is-odasi
   ```

Taslak için `--scale=0.5` kullanın; 39 sn'lik video yaklaşık 100 sn'de çıkar. Bir parçayı render etmek için `--from=10 --to=20` ekleyin.

## Ölçülmüş stil

Stil, ölçülerek kuruldu. Bu tarzdaki en çok izlenen 10 Short (9,8 – 35 milyon izlenme) kare kare ölçüldü: kesmeler, kameranın itme ve kaydırma hızı, kontrast, ışık kaynaklarının görünürlüğü, halenin genişliği, gölgenin parlaklığı ve rengi, renk ailelerinin payı, çizgi kalınlığı, kafaların ışığı ve kadrajdaki yeri, görüntünün dönmesi, titreme. Sonuçlar `STIL_KITABI.md` ve `analiz/` içinde, ham sayılar `analiz/veri/` içinde.

Örnek video İs Odası aynı yöntemle ölçüldü. Bütün videonun ölçülerinden referans aralığının dışında kalan yok:

| Ölçü | Referans (ortanca) | İs Odası |
|---|---|---|
| Kameranın durduğu kareler | %1 – 7 (3) | %1,8 |
| İçeri itme hızı | kare başına %0,25 – 0,37 (0,28) | 0,28 |
| Kontrast | 0,57 – 0,81 (0,62) | 0,72 |
| Işık kaynağı görünen kareler | %32 – 88 (75) | %77 |
| Sıcak / soğuk renk payı | %49 / %46 | %41 / %41 |
| Lambanın halesi, 40 px ötede | 0,37 | 0,36 |
| İnce çizgilerin payı | %60 – 82 (72) | %67 |

Repoda başkasına ait video yok. `referans/` klasöründe yalnızca, üstüne ölçüm işlenmiş, küçük boyutlu birkaç inceleme karesi var.

## Analiz raporları

`analiz/` klasöründe yedi rapor var: ışık, renk, karakter, çizgi, derinlik, hareket, doku. Her biri aynı şeyi yapıyor: bir ölçümü önce referans videolarda, sonra örnek videoda aynı yöntemle alıyor, hedef aralığı ve kuralları yazıyor. Kendi videonuzu yaparken hedef aralıklar için bu raporlara bakın. [analiz/README.md](analiz/README.md) hepsinin dizinini ve örnek videonun nerede durduğunu veriyor.

## Önce ölçün, sonra izleyin

Ölçüm sizi doğru aralığa getirir ama her şeyi görmez. İs Odası'nda sayılar tuttuktan sonra videoyu izleyince şunlar çıktı:

- kafalar beyaz değil krem rengiydi,
- sarığın tepesi ve eldeki tomar düz bir çizgiyle kesikti (karakter tuvali dardı),
- hattatın eli bir yerde, kalem başka bir yerdeydi,
- pencerelerin dışı düz bir renkti,
- açılışta karakter 5 saniye öylece duruyordu,
- bir pencere çerçevesi titriyordu (iki yüzey aynı düzlemdeydi),
- kalem bazı karelerde çizginin sonuna zıplıyordu,
- ışık düzdü ve gözler nokta gibiydi.

Son ikisi aslında ölçülebiliyor. Bir şey "göze düz geliyorsa" önce onu gösterecek bir sayı arayın.

Hepsinin sebebi ve çözümü `STIL_KITABI.md` dosyasının sonundaki tabloda. Motor artık bunlar için hazır parçalar içeriyor: 3B kol (`Arm3D`), pencere manzarası (`vistaMat`), tek parça delikli duvar (`holedWall`), ışık halesi ve gerçek gölgeler (`post.js`), ışık huzmesi (`beam`), 3B kandil (`kandil`).

## Lisans

Kod ve dokümanlar MIT lisanslı. Hikâyeleriniz, karakterleriniz ve sesiniz size aittir.

`referans/` klasöründeki kolajlarda yer alan referans kareleri, sahiplerinin eseridir ve MIT lisansının kapsamında değildir. Yalnızca inceleme ve karşılaştırma amacıyla, küçük boyutta ve üzerine ölçüm işlenerek konmuştur. Referans videolarını yalnızca çalışma için kullanın; yeniden yayınlamayın.

---

### English (short)

Egg-head 2D characters in a 3D world, made from code with Claude:

- three.js world, Canvas 2D character cards with lidded eyes and ten expressions
- an own ink-outline, lens-blur and bloom pass; real cast shadows, the flat characters' included
- frame-exact capture with puppeteer and ffmpeg

There is no Remotion and no Blender. The style is measured: 10 reference Shorts frame by frame (camera, light, glow, colour families, line widths, faces), with the target ranges in `STIL_KITABI.md` and `analiz/`, raw numbers in `analiz/veri/` and annotated reference sheets in `referans/`.

The sample story is in `stories/is-odasi` (finished video: `ornek/is-odasi.mp4`). Start with `SKILL.md`; Codex and other agents get there through `AGENTS.md`. Setup: `cd engine && npm install`, `pip install -r requirements.txt`, ffmpeg, Chrome (or `CHROME_PATH`).

---
**Vendored copy.** This folder is a copy of [kodlaciz/yumurta-stili](https://github.com/kodlaciz/yumurta-stili)
(MIT, © 2026 Kodla Çiz; see `LICENSE`), with local changes for the sanatolya channel: headless Linux launch flags
(`--no-sandbox`, SwiftShader via `SWGL=1`), extra hats/hair/props for antiquity, and the story `stories/troy-en`.
The sample video and the annotated reference frames are not included.
