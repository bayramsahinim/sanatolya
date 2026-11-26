# Işık

> **Nasıl okunur.** "Referans" sütunu, bu tarzdaki en çok izlenen 10 Short'un ölçümü: ortanca, parantez içinde en düşük – en yüksek. "İs Odası" sütunu, bu repodaki örnek videonun ölçümü. Ham sayılar [`veri/`](veri/) klasöründe (`isik_*.json`, `kafa_referans.json`). Ölçüm işlenmiş örnek kareler: [`../referans/isik.jpg`](../referans/isik.jpg).

## Özet

| Ölçüm | Referans (10 video) | İs Odası |
|---|---|---|
| Kontrast (aydınlık uç − karanlık uç) | 0,62 (0,57 – 0,81) | 0,72 |
| Parlak piksel (parlaklık > 0,92) | %1,2 (%0,1 – %5,2) | %3,4 |
| Işık kaynağı görünen kareler | %75 (%32 – %88) | %77 |
| Sıcak ve soğuk ton aynı karede | %25 (%1,5 – %57) | %19 |
| Gölge / aydınlık, aynı yüzeyde (parlaklık) | 0,46 (lamba konisi düşen yeşil duvar, r05) | 0,31 (hattatın duvarı) |
| Gölgenin rengi | aydınlığa göre maviye kayıyor (R 0,42, B 0,50) | mavi (#3a4063); aydınlık kısım sıcak (#8c6d6a) |
| Hale: kaynaktan 4 / 10 / 20 / 40 px ötede kalan parlaklık | 0,66 · 0,55 · 0,45 · 0,37 | 0,74 · 0,62 · 0,50 · 0,36 |
| Kafanın parlaklığı (HSV V) | 0,98 (0,89 – 1,00) | 0,96 – 1,00 (elle, 6 kafa) |
| Kafanın renk tonu (HSV S) | 0,09 (0,00 – 0,24) | 0,00 – 0,09 (elle, 6 kafa) |
| Kafada yandan yana parlaklık farkı | 0,08 (0,02 – 0,11) | ölçülemedi (şapkalı ve sakallı kafalar); gölge rengi aydınlığın 0,84 – 0,90 katı |

Referansta kafalar her videoda otomatik bulunup ölçüldü (10 videoda 411 kafa). Hale ve gölge / aydınlık oranı tek bir karede, elle seçilen noktada ölçüldü.

"Sıcak ve soğuk ton aynı karede" ölçüsü sıcak olarak yalnızca turuncu-sarıyı sayıyor. İs Odası'nın salonunda sıcak taraf kırmızı halı ve alevler; bunlar bu ölçüye girmiyor. Kırmızıyı da sayan ölçümde ([renk.md](renk.md)) bütün videoda sıcak %41, soğuk %41.

## Ne bulduk

1. **Işığın kaynağı görüntüde.** Karelerin dörtte üçünde ekranda parlayan bir şey var: tavan lambası, ay, fener, pencere.
2. **Gölge, aydınlığın yarısı kadar parlak; rengi de farklı.** Lamba konisinin düştüğü yeşil duvarda gölge, aydınlığın 0,46'sı. Mavi kanal kırmızıdan daha çok korunuyor (0,50'ye 0,42): gölge maviye kayıyor, kahverengiye değil.
3. **Işık lekesi bir renk değişimi.** Soğuk renkli yüzeye sıcak ışık vuruyor; leke, duvarın daha açık bir tonu değil, başka bir renk. Sıcak duvara sıcak ışık vurunca bu fark kayboluyor ve kare tek renge dönüyor.
4. **Hale geniş ve düz.** Kaynağın 20 px ötesinde parlaklığın 0,45'i, 40 px ötesinde 0,37'si duruyor (1080 genişlikte). Kaynağın hemen çevresinde biten dar, sert bir parlama bu stilde yok.
5. **Yalnızca ışık kaynakları parlıyor.** Beyaz kafalar, kâğıt ve açık renk duvarlar hale yapmıyor.
6. **Kafalar her ışıkta parlak kalıyor.** V 0,98; hiçbir videoda ortanca 0,89'un altına inmiyor. Sahnenin ışığı kafayı biraz boyuyor: lamba altında krem (#eccdb5), gündüz bembeyaz (#ffffff).
7. **Kafanın gölgesi çok hafif.** Yandan yana fark 0,08: kafa düz beyaz, gölge yalnızca ışığın gelmediği kenarda.

## İs Odası'nda nasıl kuruldu

- **Sahne başına tek ana ışık.** Salon: kandil halkaları ve güney kemerden giren ay ışığı. Mutfak: açık pencereden giren güneş. İs odası: Sinan'ın elindeki kandil ve mavi ızgara. Hattat: kafesli pencereden alçak güneş ve masa lambası.
- **Gece ortamın rengi, lambalar sıcak havuz.** Kandillerin ışığı mesafeyle hızlı sönüyor; duvarı ortamın mavi-mor ışığı aydınlatıyor.
- **Işık veren her şey beyazdan parlak.** Alev ve camlar 1'in üstünde bir renkle veriliyor; parlama yalnızca 1'in üstünü büyütüyor (`engine/src/post.js`). Parlama beş kat; ağırlık geniş katlarda, üstünde yumuşak bir omuz var, böylece kaynağın çevresi beyaza yanmadan hale genişliyor.
- **Yakın kandillerde ışık halkası.** Kameranın yaklaştığı kandillerde ayrıca geniş, yumuşak bir halka var (`kandil({ halo })`, `fx.glow`). Halkanın en parlak yeri camın hemen dışında (yarıçapının %28'i); ilk 20 px'i parlama taşıyor. Halka dünyada sabit boyda olduğu için yakın planda kareyi doldurabiliyor: is odasında 0,18 katına kısık (`haloK`), yoksa mavi-mor odayı turuncuya boyuyor.
- **Karakterler gerçek gölge düşürüyor.** Her karakterin görünmeyen bir gölge kartı var ve ışığa dönük duruyor (`castFrom`); siluet yere ve duvara düşüyor. Altında ışığın ters yönüne kaymış yumuşak bir leke de var.
- **Işık deseni.** Pencere kafesi ve ızgara, ışığın önüne konan bir maskeyle (`gobo`) duvara ve karaktere düşüyor.
- **Kafanın gölgesi lavanta**, aydınlığın yaklaşık 0,89 katı: gece `#d6d1f2`, gündüz `#e8e3f4`.
- **Ortam gölgesi (SSAO) yok.** Nesnelerin yere değdiği yer çizgiyle ve düşen gölgeyle anlatılıyor.

## Referanstan ayrılan yerler

- Parlak piksel %3,4: aralığın içinde, ortancanın üstünde. Hikâyede kandil ve alev çok.
- Gölge / aydınlık oranı 0,31: kuralın (0,3 – 0,5) alt ucunda.
- Halenin kaynağa en yakın kısmı (4 ve 10 px) referanstan biraz geniş: 0,74 ve 0,62; referansta 0,66 ve 0,55.

## Kurallar

1. Her sahnede görünen tek bir ana ışık.
2. Gölge = aynı yüzeyin aydınlığının 0,3 – 0,5 katı; rengi ortamın rengine kayar.
3. Sıcak ışık soğuk renkli yüzeye vursun (ya da tersi). Aynı renkteki ışık ve yüzey tek renk verir.
4. Işık veren her şeyin rengi 1'in üstünde; halesi geniş (1080 genişlikte 40 px ötede parlaklığın üçte biri). Kameranın yaklaştığı lambaya ayrıca yumuşak bir ışık halkası ver; halka kareyi dolduruyorsa gücünü düşür.
5. Kafa her ışıkta V ≥ 0,86; gölgesi lavanta, 0,89 kat.
6. Ortam gölgesi (SSAO) ekleme.
