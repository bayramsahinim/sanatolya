# Ölçüm verisi

Raporlardaki sayıların ham hâli. Her konu için iki dosya var: `*_referans.json` (10 referans Short, `r01` – `r10`) ve `*_is-odasi.json` (örnek video İs Odası; sahnelere bölünmüşse `salon`, `mutfak`, `is_odasi`, `hattat`, bütün video `tumu`).

Ortak kurallar: kareler 1080 × 1920 videodan alındı; altyazı bandı (yüksekliğin yaklaşık %60 – 80'i) hiçbir ölçüme girmiyor. Parlaklık 0 – 1 arası, renk Lab (C* = renk yoğunluğu, a* + kırmızıya, b* + sarıya / − maviye).

| Dosya | Alanlar |
|---|---|
| `kamera_*.json` | `sabit_pct` kameranın durduğu kareler · `itme_pct` / `cekme_pct` içeri itme / geri çekme olan kareler · `kaydirma_pct` yana kayma olan kareler · `itme_hizi_pct_kare` itme hızı (kare başına %, ortanca) · `kaydirma_p90_px` yana kayma (px / kare, %90'lık dilim) · `parlaklik_p50` / `parlaklik_p5` · `C_p90` renk yoğunluğu (%90'lık dilim) · `karanlik_px_pct` parlaklığı 0,08'in altındaki pikseller |
| `isik_*.json` | `kontrast` parlaklığın %95'lik dilimi − %5'lik dilimi · `parlak_pct` parlaklığı 0,92'nin üstündeki pikseller · `koyu_pct` · `sicak_pct` / `soguk_pct` doygun piksellerde turuncu-sarı / mavi-mor payı · `ikili_pct` sıcak ve soğuğun aynı karede bulunduğu kareler · `isikli_pct` içinde ışık kaynağı görünen kareler · `hale` kaynağın çevresinde 4 / 10 / 20 / 40 px ötede kalan parlaklık (`cekirdek` = kaynağın yarıçapı, px) · `golge_aydinlik` aynı yüzeyin gölgedeki ve ışıktaki parlaklık oranı |
| `renk_*.json` | `y_p1` … `y_p99` parlaklık dilimleri · `murekkep_pct` ince koyu çizgi olan pikseller · `zemin_p5` çizgiler sayılmadan en koyu yüzeyler · `s_p50` doygunluk · `c_p50` / `c_p90` aydınlık yüzeylerin renk yoğunluğu · `siyah` / `beyaz` karenin en koyu / en açık %0,5'inin rengi (RGB) · `golge_a` / `golge_b` gölgelerin rengi (a*, b*) · `golge_pay` gölgede kalan pikseller · `kose` köşe / merkez parlaklığı (vinyet) · `yerel_kontrast` ince ayrıntı |
| `ton_*.json` | altı renk ailesinin payı (`kirmizi`, `sari-turuncu`, `yesil`, `camgobegi`, `mavi`, `mor-pembe`; doygunlukla ağırlıklı) · `en_buyuk` karedeki en büyük ailenin payı · `aile` karenin en az %10'unu tutan aile sayısı |
| `cizgi_*.json` | `p25` / `p50` / `p75` çizgi kalınlığı (px) · `ince` (≤ 4 px) / `orta` (4 – 8 px) / `kalin` (> 8 px) çizgilerin payı · `pay` çizgilerin karedeki payı (%) |
| `kafa_referans.json` | bulunan kafa sayısı · `V` / `S` kafanın parlaklığı ve doygunluğu (HSV) · `yan` yandan yana parlaklık farkı · `ust` üstten alta fark · `gen` kafa genişliği / kare genişliği · `tepe` kafanın tepesi (karenin üstünden, yüksekliğin oranı) · `renk` kafanın ortanca rengi |
| `donme_*.json` | `donen_pct` görüntünün döndüğü adımlar · `hareket_10sn` 10 saniyede dönme hareketi (aynı yönde en az 1,5°) · `aci_p50` hareketin açısı · `sure_p50` süresi (kare) · `olculen_pct` ölçülebilen süre |
| `titreme_*.json` | `titrek_pct` kareden kareye titreyen piksellerin payı (bir kare önceki ve sonraki kareden zıt yönde en az 10 / 255 ayrılan) · `en_kotu` en kötü 1 saniye |
