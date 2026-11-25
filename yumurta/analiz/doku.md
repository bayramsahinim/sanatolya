# Doku: yüzeylerin boyanması

> **Nasıl okunur.** "Referans" sütunu, bu tarzdaki en çok izlenen 10 Short'un ölçümü: ortanca, parantez içinde en düşük – en yüksek. "İs Odası" sütunu, bu repodaki örnek videonun ölçümü. Ham sayılar [`veri/`](veri/) klasöründe (`renk_*.json`, `cizgi_*.json`).

## Ölçüm

Dokunun kendisi doğrudan ölçülmüyor; iki ölçü onu dolaylı gösteriyor: karedeki ince ayrıntı (yerel kontrast) ve çizgiler.

|  | Referans (10 video) | İs Odası |
|---|---|---|
| İnce ayrıntı (yerel kontrast) | 0,062 (0,042 – 0,081) | 0,059 (salonda 0,058) |
| Çizgilerin karedeki payı | %3,0 (%1,1 – %5,8) | %1,6 |
| İnce çizgilerin (≤ 4 px) payı | %72 (%60 – %82) | %67 |

## Ne bulduk

1. **Yüzey "lekelenmiş" değil "boyanmış".** Düz renk alanları ve üstlerinde ince çizgiler: fotoğraf dokusu, kum, gürültü yok.
2. **Çizgi çok ama ince ve açık.** Yüzeyler çok çizgi taşıyor ama bu çizgiler yüzeyin koyu bir tonu; bu yüzden karakterlerin siluetiyle yarışmıyor.
3. **Ayrıntıyı derz değil desen veriyor.** Düz bir duvarın taşlarını küçültmek ya da derzlerini koyulaştırmak ince ayrıntı ölçüsünü oynatmıyor. Ölçü, desenli yüzeyler (çini, boyalı kuşak, halı motifi) ve küçük nesnelerle (çıta, pano, korkuluk) yükseliyor.

## Kitteki dokular (`engine/src/paint.js`)

Hepsi resim dosyası kullanmadan, Canvas 2D ile çiziliyor.

| Doku | Ne çiziyor |
|---|---|
| `stoneTex` | her taş kendi tonunda (±%10), ince ve taş renginde derz (taş renginin 0,42 katı), üstte ve solda açık, altta koyu kenar şeridi, benek, her beş taştan birinde çatlak |
| `woodTex` | ince ve koyu tahta arası (ahşap renginin 0,36 katı), açık / koyu kenar, uzun yumuşak damar, ek yeri ve çiviler |
| `wallTex` | bütün duvarda ince kesme taş derzleri; taş boyu parametre (`ashlar`), derz taş renginin 0,4 katı |
| `carpetTex` | ince baklava dokuması, her saf için desenli kenar şeridi, her yer için kandilli bir niş, nişlerin arasında yıldız; her motifin çevresinde zeminin koyu tonuyla ince çizgi |
| `ciniTex` | tekrar eden çini, madalyonlu ya da sekiz köşeli yıldızlı; açık zemin, üç sır rengi, her biçimin çevresinde ince koyu çizgi |
| `frizTex` | duvarın ortası için boyalı kuşak: birbirine geçen iki şerit, halkalarda çiçek ya da yaprak, altın kenar |
| `domeTex` | kubbe açılımı (8192 × 3072): tepe madalyonu, güneş ışınları, palmet kuşağı, kıvrım dal, 28 kemerli pencere; her biçimin ince dış çizgisi, aralarda altın yıldızlar |
| `sootTex` | is tutmuş sıva |

## İs Odası'nda nasıl kuruldu

- **Salon:** duvarların ve ayakların dibinde 92 cm'lik çini kuşağı, duvarın ortasında 1 m'lik boyalı kuşak, küçük odanın penceresinin çevresinde ve güney pencerelerinin üstünde çini pano. Hepsi duvarın 5 cm önünde ve kenarlarında gerçek bir pervaz var: duvarla aynı düzlemde duran bir yüzey titrer. Hiçbiri bir kafanın arkasına gelmiyor.
- **Geometriyle gelen ayrıntı:** kemer taşlarının arasında oluk, ayaklarda başlık, kepenklerde çıta, kapı kanatlarında pano, iskelede korkuluk (bkz. [cizgi.md](cizgi.md)).
- **Çözünürlük:** 30 m'lik duvar 3072 px; 8 m'den bakınca doku pikseli başına yaklaşık 2,5 ekran pikseli. Taş ve ahşap 1024 px.
- **İs odası bilerek desensiz:** is tutmuş sıva. O sahnenin ince ayrıntısı karakterlerden ve kandilden geliyor.

## Kurallar

1. Önce düz renk alanları, sonra ince çizgiler. Gürültü ve fotoğraf dokusu yok.
2. Boyalı çizgi ekranda 3 – 5 px; rengi yüzeyin koyu tonu.
3. Her parçanın (taş, tahta) bir açık, bir koyu kenarı olsun.
4. Büyük her duvara desen ver: çini kuşağı, boyalı kuşak ya da pencere çevresinde pano. Deseni duvarın birkaç santim önüne as, kenarına pervaz koy.
5. Desenleri açık dolgu ve ince koyu dış çizgiyle çiz; koyu dolgu dış çizgisiyle birleşip kalın bir çizgiye dönüşür.
6. Doku yakın planda ekranda birkaç kattan fazla büyümesin; gerekiyorsa dokuyu büyük çiz.
