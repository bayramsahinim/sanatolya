# Analiz raporları

Bu klasör, stilin sayılara dökülmüş hâli. Her rapor bir konuyu alıyor: önce referans videolarda ölçüyor, sonra aynı ölçümü örnek videoda (İs Odası) yapıyor, hedef aralığı ve kuralları yazıyor.

| Rapor | Konu |
|---|---|
| [isik.md](isik.md) | Ana ışık, gölgenin parlaklığı ve rengi, hale, kafaların ışığı |
| [renk.md](renk.md) | Parlaklık dağılımı, en koyu yüzeyler, renk aileleri, gölge rengi, vinyet |
| [karakter.md](karakter.md) | Kafa biçimi, dış çizgi, göz, kaş, ağız, oranlar, göz kırpma |
| [cizgi.md](cizgi.md) | Mürekkep çizgilerinin kalınlığı ve hangi kenarlara çizildiği |
| [derinlik.md](derinlik.md) | Arka plan bulanıklığı, ön plan nesneleri, kafanın kadrajdaki yeri |
| [hareket.md](hareket.md) | Kamera, kesme, görüntünün dönmesi, titreme |
| [doku.md](doku.md) | Yüzeylerin boyanması |

Stilin kısa özeti ve metin kalıbı: [../STIL_KITABI.md](../STIL_KITABI.md). Ölçüm işlenmiş referans kareleri: [../referans/](../referans/). Ham sayılar: [veri/](veri/).

## Neyi, nasıl ölçtük

- **Referans:** Bu tarzdaki (beyaz yumurta kafalı karakterler, 3B dünya) en çok izlenen 10 Short: 9,8 – 35 milyon izlenme, toplam 593 sn, 17.734 kare, 1080 × 1920. Videolar repoda yok; raporlarda `r01` – `r10` olarak geçiyorlar.
- **Örnek video:** İs Odası (38,8 sn), dört sahneye bölünerek: salon, mutfak, is odası, hattat.
- **Yöntem:** Referans ve örnek video aynı yöntemle, aynı ayarla ölçüldü. Altyazı bandı (yüksekliğin yaklaşık %60 – 80'i) hiçbir ölçüme girmiyor; yoksa beyaz yazı "ışık", konturu "çizgi" sayılır.
- **Sayıların kaynağı:** Raporlardaki sayılar `veri/` klasöründeki ölçüm dosyalarından alındı; alanların anlamı [veri/README.md](veri/README.md) içinde.

## İs Odası nerede duruyor

Bütün videonun ölçülerinden referans aralığının dışında kalan yok. Ortancadan belirgin ayrılanlar ve sebepleri:

| Ölçü | Referans ortancası | İs Odası | Sebep |
|---|---|---|---|
| Orta parlaklık | 0,40 | 0,29 | Hikâyenin %60'ı gece geçiyor; referansın gece videoları 0,16 – 0,21 |
| Çizgilerin karedeki payı | %3,0 | %1,6 | Gece karelerinde koyu duvarın üstündeki çizgi ölçüme girmiyor |
| Parlak piksel | %1,2 | %3,4 | Kandil ve alev çok |
| Görüntünün dönmesi (10 sn'de) | 0,6 | 1,8 | Kubbeye dik bakan iki plan; kamera yatmıyor |

## Ölçümün göremediği

Ölçüm doğru aralığa getiriyor ama her şeyi görmüyor. İs Odası'nda sayılar tuttuktan sonra izleyince bulunanlar: kesik şapka, kalemden ayrı duran el, düz renkli pencere, titreyen pencere kasası, zıplayan kalem, eksik bir zemin. Hepsinin sebebi ve çözümü [../STIL_KITABI.md](../STIL_KITABI.md) sonundaki tabloda. Bir şey "göze yanlış geliyorsa" önce onu gösterecek bir sayı arayın, sonra yine izleyin.
