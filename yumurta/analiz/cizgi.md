# Çizgi

Stilin en tanınan özelliği: 3B dünyanın kenarlarında ince siyah mürekkep çizgileri, karakterlerde daha kalın mürdüm rengi bir dış çizgi.

> **Nasıl okunur.** "Referans" satırları, bu tarzdaki en çok izlenen 10 Short'un ölçümü: ortanca ve en düşük – en yüksek. "İs Odası" satırları, bu repodaki örnek videonun ölçümü. Ham sayılar [`veri/`](veri/) klasöründe (`cizgi_*.json`). Çizgilerin kalınlığa göre boyandığı örnek kareler: [`../referans/cizgi.jpg`](../referans/cizgi.jpg).

## Ölçüm

İki saniyede bir kare, tam boyutta (1080 × 1920). Çevresinden belirgin biçimde koyu, ince yapılar bulunuyor ve her birinin kalınlığı ölçülüyor. Çizgiler alanla değil adetle sayılıyor, böylece kalın tek bir dış çizgi on ince çizgiyi bastırmıyor. Karakter çizgileri, dünya çizgileri ve dokuya boyanmış çizgiler birlikte sayılıyor.

|  | Ortanca kalınlık | İnce (≤ 4 px) | Orta (4 – 8 px) | Kalın (> 8 px) | Çizgilerin karedeki payı |
|---|---|---|---|---|---|
| **Referans, ortanca** | 2,5 px | %72 | %15 | %12 | %3,0 |
| Referans, aralık | 2 – 3 px | %60 – %82 | %9 – %21 | %7 – %22 | %1,1 – %5,8 |
| İs Odası · Salon (gece, kandil) | 3 px | %69 | %23 | %8 | %2,4 |
| İs Odası · Mutfak (gündüz) | 3 px | %82 | %17 | %1 | %0,7 |
| İs Odası · İs odası (gece, fener) | 7 px | %33 | %24 | %43 | %1,8 |
| İs Odası · Hattat (gündüz) | 4 px | %64 | %31 | %5 | %1,4 |
| **İs Odası · bütün video** | 3 px | %67 | %23 | %9 | %1,6 |

## Ne bulduk

1. **Dünya çizgisi ince.** Referansta ortanca 2,5 px; çizgilerin dörtte üçü 4 px'ten ince. Kalın çizgiler çoğunlukla karakterlerin dış çizgisi.
2. **Çizgi çok ama ince.** Çizgiler karenin %3'ünü tutuyor. Kalın birkaç çizgi değil, çok sayıda ince ayrıntı çizgisi var: kemer taşları, tahta araları, desen kenarları.
3. **Çizgi keskin.** Arka plan bulanıksa çizgisi de onunla birlikte bulanık; yani çizgi, alan derinliğinden önce çiziliyor.
4. **Karakter kartlarının çevresinde dünya çizgisi yok.** Karakterin kendi dış çizgisi var; çift çizgi görünmüyor.
5. **Dokuya boyanan çizgi mürekkep değil.** Taş derzi, tahta arası gibi çizgiler yüzeyin koyu bir tonu; mürekkepten ince ve açık.

## Motor nasıl çiziyor

- **Dünya çizgisi** derinlik sıçramasından (bir nesne arkasındakinin önünde) ve yüzey yönündeki kırılmadan (köşe) çıkıyor. Ekranda neredeyse sabit kalınlıkta: 1080 genişlikte yakında 3,4 px, uzakta 2,2 px (`inkNear`, `inkFar`); köşe çizgisi daha ince. Lens bulanıklığından önce çiziliyor, karakter kartlarına çizilmiyor (`engine/src/post.js`).
- **Karakterin dış çizgisi** mürdüm (`#2a1a2c`), karedeki en kalın çizgi; üstte ince, altta ve ışığın gelmediği yanda kalın (bkz. [karakter.md](karakter.md)).
- **Geometriyle gelen çizgi.** Kemer taşlarının kenarına pah kırılıyor (`voussoirArch({ bevel })`): iki taş arasında V biçiminde bir oluk var ve mürekkep geçişi her oluğa bir çizgi çekiyor. Derz boya değil geometri olduğu için her uzaklıkta ince kalıyor. Kepenk çıtası, kapı panosu, iskele korkuluğu, ayak başlığı aynı işi görüyor.
- **Desenler açık dolgu, ince koyu dış çizgi.** Koyu bir dolgu kendi dış çizgisiyle birleşip tek, kalın bir çizgi gibi okunuyor.
- **İnce nesneler gerçekten ince.** Kandil halkasının demiri 6 cm, askı çubukları 2,2 cm; daha kalınları genel planlarda kalın çizgi gibi sayılıyor.

## Ölçümün sınırı

- **Gece karelerinde dünya çizgilerinin çoğu sayılmıyor.** Duvar koyuysa çizgi çevresinden yeterince ayrışmıyor; sayılanların çoğu beyaz kafaların çevresindeki kalın dış çizgi. Neyin sayıldığından emin olmak için çizgi piksellerini kalınlığına göre boyayıp bakın ([`../referans/cizgi.jpg`](../referans/cizgi.jpg) böyle üretildi).
- **İs odasında kalın çizgi payı %43.** O sahnede iki karakter kadrajın yarısını dolduruyor, dış çizgileri büyüyor; duvarlar da koyu. Referansın yakın plan ağırlıklı videosunda (r05) kalın çizgi payı %15.
- Bütün videoda ölçülerin hepsi referans aralığının içinde. Çizgilerin karedeki payı (%1,6) ve ince çizgilerin payı (%67) ortancanın altında; hikâyenin büyük kısmı gece geçiyor.

## Kurallar

1. Dünya çizgisi 1080 genişlikte 3,4 px (yakın) – 2,2 px (uzak); köşelerde daha ince.
2. Çizgi alan derinliğinden önce çizilir, karakter kartlarına çizilmez.
3. Dokuya boyanan çizgi, mürekkepten ince ve açık olur: yüzey renginin 0,36 – 0,55 katı.
4. Karedeki en kalın çizgi karakterin dış çizgisidir.
5. Boyalı çizgi yüzeyle birlikte büyür: dokudaki 9 px'lik çizgi, yüzey yakındayken ekranda 20 px olur. Çizgiyi kalın değil, dokuyu büyük çizin.
