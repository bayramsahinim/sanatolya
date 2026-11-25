# Karakter

> **Nasıl okunur.** "Kit" sütunu, `engine/src/toon.js`'in çizdiği değerler (kafa genişliğine oranla). "Referansla karşılaştırma" sütunu, referans videolardan kesilen 8 yakın plan kafayla yan yana bakıldığında görülen. Kafaların ışık ölçümü için [isik.md](isik.md), kadrajdaki yeri için [derinlik.md](derinlik.md). Ölçüm işlenmiş yakın planlar: [`../referans/karakter.jpg`](../referans/karakter.jpg).

## Kafa ve yüz

|  | Kit | Referansla karşılaştırma |
|---|---|---|
| Kafa yüksekliği / genişliği | 0,935 | genişliği yüksekliğinden fazla |
| Biçim | elips değil: tepe hafif sivri, çene dolgun, çeneye doğru %11 daralıyor (süper elips; tepe üssü 1,75, çene üssü 2,3) | tutuyor |
| Yüzün döndüğü yanda şişkinlik | %8 | tutuyor |
| Karakterden karaktere fark | her karakterin biçimi biraz farklı (görünüşünden türetilen tohum) | – |
| Dış çizgi kalınlığı | üstte %2,7, altta %6,5 (ortalama %3,9) | altta ve ışığın gelmediği yanda belirgin kalın |
| Çizgi rengi | koyu mürdüm `#2a1a2c` | siyah değil, mürdüm |
| İki gözün arası (merkezden merkeze) | 0,28 | 0,25 – 0,31 |
| Varsayılan göz | düz bir kapak çizgisinden sarkan koyu yarım daire: 0,13 genişlik, 0,09 – 0,10 yükseklik; kapak çizgisi 0,17 | göz, yüksekliğinden geniş |
| Şaşkın göz | birbirine değen iki beyaz daire, çap 0,22, ortalarında küçük birer nokta | tutuyor |
| Kaş | 0,18 uzun, 0,049 kalın, uçları ince | gözün epey üstünde; çoğu zaman biri diğerinden yüksek |
| Ağız | gözlerin 0,19 altında; düz hâli 0,10 genişlikte kısa, eğik bir çizgi | tutuyor |
| Yüzün bakış yönüne kayması | 0,10 | bütün yüz bakılan yana kayıyor (3/4 dönüş) |
| Allık, gözde parlama noktası | yok | yok |
| Kafanın gölgesi | ışığın gelmediği kenarda yumuşak hilal; gece 0,84, gündüz 0,90 kat; lavanta | tutuyor |

## Gövde

|  | Kit |
|---|---|
| Toplam boy | 3,55 kafa |
| Gövde genişliği / kafa genişliği | 0,67 |
| Bacak ve kol | tek koyu çizgi, kafa genişliğinin %4,7'si |
| El | başparmağı belli küçük eldiven, çap 0,12 |
| Gövdenin gölgesi | aydınlıktan gölgeye yumuşak geçiş, 0,62 kat |
| Şapka | kafanın üst kısmını örter, alt kenarı kafatasını izler; yüz şapkadan sonra çizilir (yoksa kaşlar kaybolur) |

## Hareket

|  | Kit | Referansla karşılaştırma |
|---|---|---|
| Göz kırpma aralığı | 0,9 – 2,4 sn (`blinkAt`) | r05'in yakın planında kare kare sayım: yaklaşık 1 – 2 sn'de bir |
| Göz kırpmanın biçimi | 4 kare: yarım, kapalı, kapalı, yarım | 2 – 3 kare kapalı |
| İfade değişirken | değişim bir göz kırpmanın içinde | – |
| Beklerken | hiç hareket yok; nefes, sallanma, döngü yok | – |
| Tepkinin kelimeye göre zamanı | kelimeden 2 kare önce (`A('kelime')`) | – |
| Konuşan ağız | sesin zarfına göre açılıp kapanıyor (`flap`) | 2 – 3 karede bir açılıp kapanıyor |
| Çizgi titremesi, esneme-büzülme | yok | yok |

## Ne bulduk

1. **Göz ne nokta ne oval.** Yakın planlarda göz, kapak çizgisinden sarkan yarım daire: yüksekliğinden geniş. Gözler birbirine yakın: kafa genişliğinin yaklaşık 0,28'i.
2. **Kafa "yumurta" değil, hafif köşeli bir fasulye.** Elipsi bozan üç şey: sivrice tepe, dolgun çene, yüzün döndüğü yanda şişkinlik. Kafayı elle çizilmiş gösteren şey yuvarlak olmaması değil, simetrik olmaması.
3. **Dış çizgi tek kalınlıkta değil.** Altta ve gölge yanında üstteki kalınlığın iki üç katı. Karakteri "yapıştırma" gibi göstermeyen ayrıntı bu.
4. **Göz kırpma sık.** Yakın planda 1 – 2 saniyede bir.
5. **İfade sahne boyunca aynı kalmıyor.** Her önemli kelimede değişiyor: şaşkınlık → kızgınlık → sırıtış.

## Kendi kuralımız olarak kalanlar

- **Kafalar her sahnede beyaz.** Referansta lamba altında kafa kreme dönüyor (S 0,21 – 0,24). Bizde kafa beyaz kalıyor; lambanın ışığı yalnızca o yandaki kenara hafif bir sıcaklık veriyor (`rim`). Krem kafalar "kirli" görünüyor.
- **Bir şeye dokunan kol 3B** (`Arm3D`): kalem, kandil, karıştırma çubuğu gerçekten elde.
- **Kumaş çizgileri koyu.** Sarığın ve aşçı başlığının sargı çizgileri koyu mor ve ince; beyaz kumaşın üstündeki açık gri çizgi, çizgi olarak değil gölge olarak okunuyor.

## Kurallar

`engine/src/toon.js` bu değerlerle çiziyor. Yeni bir karakter eklerken `node faces.mjs <hikâye> --zoom` ile bütün ifadeleri tek sayfada görün ve referans yakın planlarıyla yan yana koyun.
