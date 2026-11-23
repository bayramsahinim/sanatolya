# Hareket: kamera ve kurgu

> **Nasıl okunur.** "Referans" sütunu, bu tarzdaki en çok izlenen 10 Short'un ölçümü: ortanca, parantez içinde en düşük – en yüksek. "İs Odası" sütunu, bu repodaki örnek videonun ölçümü. Ham sayılar [`veri/`](veri/) klasöründe (`kamera_*.json`, `donme_*.json`, `titreme_*.json`). Kamera hareketinin kare kare işlendiği şerit: [`../referans/kamera.jpg`](../referans/kamera.jpg).

## Kamera

Her kare 180 × 320'ye küçültülüp bir öncekiyle karşılaştırıldı. Yavaş itmeyi görebilmek için 10 kare arayla, 41 yakınlaşma adımında ölçüldü.

| Ölçüm | Referans (10 video) | İs Odası |
|---|---|---|
| Sabit kamera (karelerin %'si) | %3 (%1 – %7) | %1,8 |
| Kaydırma olan kareler | %86 (%77 – %94) | %85 |
| İçeri itme hızı (kare başına) | %0,28 (%0,25 – %0,37) | %0,28 |
| Karanlık piksel (< %8) | %0,6 (%0,2 – %15) | %0,4 |
| Renk yoğunluğu (C*, %90) | 49 (30 – 77) | 47 |
| Sert kesme (gözle sayıldı) | 1 (0 – 2) | 1 |

"Kesme gibi görünen" anların çoğu kesme değil: 5 – 9 karelik hızlı bir yakınlaşma ya da süzülme, yoğun hareket bulanıklığıyla. Bu yüzden sert kesmeler kare kare bakılarak sayıldı.

## İs Odası'nın kamerası

- **Geçiş:** `smoother` (5. derece yumuşak adım), 25 – 78 kare. Hızlanma ve yavaşlama simetrik.
- **Bekleyiş:** Kamera durmuyor. Her bekleyişte kare başına %0,10 – 0,30 içeri itme (`creep`) ve yana kayma (`drift`). İs odasındaki yavaş itme (%0,10) bilerek bırakıldı: daha hızlısı karakterleri kadrajın kenarına itiyor.
- **Savrulma (whip):** 3 savrulma, 9 – 10 kare, hareket bulanıklığıyla. Setler arası 30 m'den uzaksa kendiliğinden yana savrulmaya dönüyor.
- **Darbe sarsıntısı:** `kick`, 7 kare, her karede yön değiştiriyor ve sönüyor.
- **El kamerası titremesi:** yok.
- **Sert kesme:** 1.

## Görüntünün dönmesi

Kare 96 px'lik parçalara bölündü; her parçanın altı kare sonra nereye gittiği bulundu ve bu kaymalar "kayma + yaklaşma + dönme" olarak ayrıldı. Kameranın değil, görüntünün ne yaptığı ölçülüyor.

|  | Dönen adımların payı | 10 saniyede dönme hareketi | Hareketin açısı (ortanca) | Süresi (kare) | Ölçülebilen süre |
|---|---|---|---|---|---|
| **Referans, ortanca** | %5 | 0,6 | 2,4° | 17 | %62 |
| Referans, aralık | %1 – %18 | 0,0 – 1,9 | 0,0 – 5,8° | 0 – 30 | %42 – %86 |
| İs Odası (kamera hiç yatmıyor) | %12 | 1,8 | 4,0° | 27 | %73 |

- **Referansta görüntü dönüyor, ama az.** 10 saniyede ortanca 0,6 hareket (aynı yönde en az 1,5°); 2 videoda hiç yok.
- **İs Odası'nda görüntü, kamera yatmadığı hâlde dönüyor.** Neredeyse dik yukarı bakan bir kamera yana dönünce görüntü döner; bu, kubbeye bakan iki planın girişinde ve çıkışında oluyor. 10 saniyede 1,8: referans aralığının üst ucunda. Bu yüzden kameraya ayrıca yatış eklenmedi.
- **Sayım oynak.** Hareket sayısı eşiğe (1,5°) yakın birkaç dönüşe bağlı; ondalığına güvenmeyin. Hızlı hareketlerin bir kısmında parçalar birbirini kaybediyor; son sütun ölçülebilen süreyi veriyor.

## Titreme

Bir önceki ve bir sonraki kareden zıt yönde ayrılan pikseller sayıldı: bir kare parlayıp sönen ya da sönüp parlayan pikseller. Aynı düzlemdeki iki yüzey böyle titrer. İnce bir çizginin pikselin üstünden geçmesi de böyle sayılır; bu yüzden sayı tek başına bir şey söylemez, referansla karşılaştırılır ve en kötü saniyeye gidip bakılır.

|  | Salon | Mutfak | İs odası | Hattat | Bütün video | En kötü 1 saniye |
|---|---|---|---|---|---|---|
| **Referans, ortanca** | – | – | – | – | %2,53 | %6,2 |
| Referans, aralık | – | – | – | – | %1,58 – %4,57 | %4,9 – %10,1 |
| İs Odası | %1,68 | %0,89 | %0,92 | %0,65 | %1,23 | %4,1 |

Referans videolar YouTube'un sıkıştırmasından geçmiş, İs Odası doğrudan render; sıkıştırma da bu sayıyı yükseltir.

## Ne bulduk

- **Kamera durmuyor.** Sabit kare oranı %1 – 7. Her bekleyiş yavaşça içeri itiyor, çoğu yana da kayıyor.
- **Sahneler tek bir dünyada akıyor.** Kamera bir sonraki ana fiziksel olarak gidiyor; sert kesme video başına 0 – 2.
- **Açılış hızlı.** İlk 5 saniyede 3 – 4 ayrı görüntü (10 videonun 9'u); ayrıntı [../STIL_KITABI.md](../STIL_KITABI.md) içinde.
- **Işık hikâyedeki saate uyuyor.** Açıklamaya geçişte sahne gece mavisine dönmek zorunda değil; gün ↔ gece geçişi hikâyeye bağlı.
- **Düz duvarın önündeki yavaş itme ölçülemiyor.** Kare karşılaştırması, üzerinde ayrıntı olmayan bir yüzeyin önündeki yavaş hareketi göremiyor. Sahneye desen eklenince aynı kamera daha yavaş ölçülüyor; sayılar dokudan sonra yeniden alınmalı.

## Kurallar

1. Kamera hiçbir an durmaz: bekleyişte kare başına %0,15 – 0,35 itme.
2. Geçişler yumuşak hızlanıp yumuşak yavaşlar (yaklaşık 25 kare). Ani sıçrama ya kesmedir ya da hareket bulanıklıklı savrulma.
3. Darbe = 7 karelik, her karede yön değiştiren sarsıntı.
4. Video başına en fazla bir iki sert kesme.
5. Kameraya yatış ekleme; dik yukarı bakan planlar görüntüyü zaten döndürür.
