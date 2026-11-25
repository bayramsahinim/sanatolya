# Renk ve ton

Bir karenin "pahalı" ya da "ucuz" görünmesinin büyük kısmı burada. Çizim aynı kalsa bile, karanlıklar siyaha gömülüyorsa, bütün kare tek renge boyanmışsa ya da gölgeler kahverengiyse stil tutmuyor.

> **Nasıl okunur.** "Referans" sütunu, bu tarzdaki en çok izlenen 10 Short'un ölçümü: ortanca, parantez içinde en düşük – en yüksek. "İs Odası" sütunu, bu repodaki örnek videonun ölçümü (bütün videonun ortancası). Ham sayılar [`veri/`](veri/) klasöründe (`renk_*.json`, `ton_*.json`). Ölçüm işlenmiş örnek kareler: [`../referans/renk.jpg`](../referans/renk.jpg).

## Özet

15 karede bir kare, 540 × 960, altyazı bandı sayılmıyor.

| Ölçüm | Referans (10 video) | İs Odası |
|---|---|---|
| Karanlık uç (parlaklığın %5'lik dilimi) | 0,124 (0,044 – 0,200) | 0,105 |
| En koyu yüzeyler (çizgiler sayılmadan %5'lik dilim) | 0,153 (0,044 – 0,227) | 0,106 |
| Orta parlaklık | 0,402 (0,158 – 0,581) | 0,291 |
| Aydınlık uç (%95) | 0,786 (0,699 – 0,927) | 0,858 |
| En parlak (%99) | 0,928 (0,852 – 1,000) | 0,983 |
| Doygunluk (HSV, ortanca) | 0,51 (0,38 – 0,68) | 0,46 |
| Aydınlık yüzeylerin renk yoğunluğu (Lab C*, ortanca) | 31,8 (18,0 – 60,0) | 30,9 |
| Aynısı, en canlı %10 | 53,4 (36,0 – 80,4) | 57,2 |
| Çizgi payı (karenin %'si) | 2,61 (1,12 – 5,11) | 1,79 |
| İnce ayrıntı (yerel kontrast) | 0,062 (0,042 – 0,081) | 0,059 |
| Köşe / merkez parlaklığı (vinyet) | 0,67 (0,33 – 0,82) | 0,70 |
| Gölgelerin rengi: a* (+ = kırmızıya) | 13,9 (3,4 – 22,3) | 18,5 |
| Gölgelerin rengi: b* (+ = sarıya, − = maviye) | -9,3 (-26,6 – 5,0) | -12,2 |

## Renk aileleri: sıcak ve soğuk kareyi paylaşıyor

Karedeki rengin hangi aileden geldiği, doygunlukla ağırlıklandırılarak sayıldı (saniyede 2 kare). Sıcak = kırmızı + sarı-turuncu, soğuk = camgöbeği + mavi.

|  | Sıcak % | Soğuk % | Mor-pembe % | Yeşil % | Karedeki en büyük aile % |
|---|---|---|---|---|---|
| **Referans, ortanca** | 49 | 46 | 4 | 1 | 67 |
| Referans, en düşük – en yüksek | 18 – 74 | 26 – 68 | 0 – 14 | 0 – 14 | 63 – 74 |
| İs Odası · Salon (gece, kandil) | 35 | 47 | 18 | 0 | 49 |
| İs Odası · Mutfak (gündüz) | 54 | 33 | 10 | 3 | 55 |
| İs Odası · İs odası (gece, fener) | 24 | 50 | 26 | 0 | 55 |
| İs Odası · Hattat (gündüz) | 64 | 23 | 13 | 0 | 44 |
| **İs Odası · bütün video** | 41 | 41 | 17 | 0 | 49 |

- Referansta bir videonun renginin yaklaşık yarısı sıcak, yarıya yakını soğuk. **Soğuk pay hiçbir videoda %26'nın altına inmiyor; sıcak pay hiçbirinde %74'ü geçmiyor.**
- Tek renge boyanmış bir video yok. Turuncu ışık altında turuncu duvarlar (sıcak pay %90'ın üstü) bu stilin dışında.

## Sahne sahne (İs Odası)

| Sahne | Orta parlaklık | En koyu yüzey | C* ortanca | C* %90 | Köşe / merkez | Gölge a* | Gölge b* | Siyah nokta (RGB) |
|---|---|---|---|---|---|---|---|---|
| Salon (gece, kandil) | 0,31 | 0,106 | 29 | 53 | 0,79 | 20 | -13 | (24, 15, 39) |
| Mutfak (gündüz) | 0,31 | 0,099 | 19 | 37 | 0,45 | 13 | -3 | (25, 16, 32) |
| İs odası (gece, fener) | 0,18 | 0,101 | 34 | 62 | 0,36 | 24 | -26 | (26, 19, 50) |
| Hattat (gündüz) | 0,29 | 0,111 | 45 | 58 | 0,35 | 17 | -7 | (27, 19, 33) |

## Ne bulduk

1. **Gölge ortamın rengini alıyor, ışığın değil.** Gölgelerin b* değeri referansta ortanca -9 (maviye kaymış); en sarı video bile +5. Kahverengi gölge bu stilde yok.
2. **Hiçbir yüzey siyaha gömülmüyor.** Çizgiler sayılmadan en koyu yüzeylerin ortancası 0,153. Siyaha yaklaşan tek şey mürekkep çizgisi; koyu malzemeler lacivert, patlıcan moru ya da bordo.
3. **Siyah nokta mora çalıyor.** Karenin en koyu %0,5'i referansta mor (örnek: (32, 19, 32), (21, 14, 33)); İs Odası'nda (25, 16, 38).
4. **Renk yoğunluğu ölçülü.** Aydınlık yüzeylerin C* ortancası 32; referansın en canlı videosunda bile 60. Krem duvara turuncu ışık vurursa 60'ı kolayca geçiyor ve kare tek renk okunuyor.

## İs Odası'nda nasıl kuruldu

- **Salon:** Gece ortamın rengi. Kandil halkaları duvarı turuncuya boyamıyor; halının ve ayakların üstünde sıcak havuzlar yapıyor, duvarlar ve kemerler mavi-mor kalıyor. Kapı duvarına halkaların hizasından alttan sıcak bir ışık vuruyor; kapının üstü gecenin mavisinde.
- **Mutfak:** Gökten gelen dolgu ışığı mavi, alttan gelen yansıma mor, güneş sıcak. Tavanın ahşabı kahverengi değil mürdüm. Çinili duvarda orta tonda mavi yıldızlar, turkuaz baklavalar ve mercan rengi noktalar var.
- **Hattat:** Duvarlar soluk mavi-gri taş, halı mavi; kafesli pencereden giren güneş duvarda sıcak bir leke yapıyor, gölgesi duvarın kendi soğuk renginde kalıyor. Kâğıdın çevresinde mavi-altın bir çerçeve (tezhip) var, yoksa yakın planlarda krem kâğıt ve ahşap masadan başka renk kalmıyor.
- **Bütün sahneler:** Renk düzeltmesinin taban rengi (`lift`) lacivert-mor; saf siyah yok. Vinyet hafif.

## Referanstan ayrılan yerler

Renk ölçülerinden referans aralığının dışında kalan yok. Aralığın içinde, ortancanın altında kalanlar:

- Orta parlaklık 0,29; referansın ortancası 0,40. Hikâyenin %60'ı gece geçiyor; referansın en karanlık videosu 0,16.
- Mutfakta renk yoğunluğu 19; sınırın (18,0) üstünde, ortancanın (32) altında. Sahne açık renk çini ve taştan oluşuyor.
- İnce ayrıntı 0,059; referansın ortancası 0,062. Ayrıntı için bkz. [doku.md](doku.md).

## Kurallar

1. Sıcak ve soğuk kareyi paylaşsın: bir sahnede sıcak renklerin payı %75'i geçmesin (referansın en sıcak videosu %74).
2. Gölge, aynı yüzeyin aydınlık kısmının yaklaşık yarısı kadar parlak olsun ve kahverengiye değil, ortamın rengine (gece mavi-mor, gündüz hafif soğuk) kaysın.
3. Saf siyah yüzey yok. En koyu yüzey bile renkli; siyaha yalnızca çizgiler yaklaşıyor.
4. Aydınlık yüzeylerin renk yoğunluğu (C*) 20 – 50 arasında kalsın. 60'ın üstü referansta yok.
