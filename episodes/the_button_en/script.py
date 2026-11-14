"""THE BUTTON: faithful English adaptation of the Turkish source narration.

Each entry: (Turkish source sentence, English translation). Order and count match
the source exactly (one English line per Turkish sentence); `tr_segments.json`
holds where each Turkish sentence is spoken in the source video.
"""

LINES = [
    # cold open
    ("Önündeki düğmeye basarsan 50.000 dolar kazanacaksın.",
     "If you press the button in front of you, you'll win fifty thousand dollars."),
    ("Ama tanımadığın biri ölecek.",
     "But someone you don't know will die."),
    ("Kim olduğunu görmeyeceksin.",
     "You won't see who it is."),
    ("Adını bile öğrenmeyeceksin.",
     "You won't even learn their name."),
    ("Basar mıydın?",
     "Would you press it?"),
    # the story
    ("Richard Matheson'ın 1970'te yayımlanan Düğme Düğme öyküsü insanı böyle bir teklifin karşısına koyuyor.",
     "Richard Matheson's story \"Button, Button,\" published in 1970, puts you face to face with exactly this kind of offer."),
    ("New York'ta yaşayan Norma ile Arthur'ın kapısına bir paket bırakılıyor.",
     "A package is left at the door of Norma and Arthur, who live in New York."),
    ("İçinden küçük tahta bir kutu çıkıyor.",
     "Inside is a small wooden box."),
    ("Kutunun üzerinde kilitli cam bir kapağın altında tek bir düğme var.",
     "On top of the box, under a locked glass cover, there's a single button."),
    ("Yanındaki notta Bay Steward'ın akşam 8'de geleceği yazıyor.",
     "The note next to it says a Mr. Steward will come by at eight p.m."),
    ("Steward geldiğinde anahtarı masaya bırakıyor ve teklifini açıklıyor.",
     "When Steward arrives, he leaves the key on the table and explains his offer."),
    ("Düğmeye basarlarsa 50.000 dolar alacaklar.",
     "If they press the button, they'll get fifty thousand dollars."),
    ("Dünyanın bir yerinde tanımadıkları bir insan ölecek.",
     "And somewhere in the world, a person they don't know will die."),
    ("Kimin adına çalıştığınıysa söylemiyor.",
     "But who he works for, he won't say."),
    ("Arthur bu konuşmayı bitiriyor, adamı gönderiyor ve bıraktığı kartı yırtıyor.",
     "Arthur ends the conversation, sends the man away, and tears up the card he left behind."),
    ("Norma'nın aklı ise kutuda kalıyor.",
     "But Norma can't stop thinking about the box."),
    ("Ertesi gün kartın parçalarını bir araya getirip Steward'ı arıyor.",
     "The next day, she pieces the card back together and calls Steward."),
    ("Adam ölecek kişiyi tanımayacaklarını ve ölümünü görmeyeceklerini tekrarlıyor.",
     "The man repeats that they won't know the person who dies, and they won't see them die."),
    ("O akşam paket yeniden kapılarında beliriyor.",
     "That evening, the package shows up at their door again."),
    ("Norma kutuyu alıp dolaba saklıyor.",
     "Norma takes the box and hides it in the cabinet."),
    ("Yemekte konuyu açıyor.",
     "At dinner, she brings it up."),
    ("Ya teklif gerçekse?",
     "What if the offer is real?"),
    ("Arthur için cevap değişmiyor.",
     "For Arthur, the answer doesn't change."),
    ("Kurbanı tanımıyor olmaları yaptıkları şeyi değiştirmeyecek.",
     "Not knowing the victim won't change what they'd be doing."),
    ("Norma ise yıllardır ertelediklerini düşünüyor: Avrupa yolculuğunu, adadaki küçük evi, "
     "bir gün çocuk sahibi olma ihtimalini.",
     "Norma, though, thinks about everything she's put off for years: the trip to Europe, "
     "the little house on the island, the chance of having a child someday."),
    ("Ertesi sabah Arthur işe gidince kutuyu çıkarıyor.",
     "The next morning, once Arthur leaves for work, she takes out the box."),
    ("Cam kapağı açıp düğmeye basıyor.",
     "She opens the glass cover and presses the button."),
    ("Hiçbir şey olmuyor.",
     "Nothing happens."),
    ("Norma bunun saçmalık olduğuna karar verip kutuyu çöpe atıyor.",
     "Norma decides it's all nonsense and throws the box in the trash."),
    ("Fakat akşam bir hastaneden telefon geliyor.",
     "But that evening, a call comes from a hospital."),
    ("Arthur metro peronundaki kalabalığın içinde trenin önüne itilmiş ve hayatını kaybetmiş.",
     "In the crowd on a subway platform, Arthur was pushed in front of a train, and he lost his life."),
    ("Norma o anda sigortayı hatırlıyor.",
     "In that moment, Norma remembers the insurance."),
    ("Kocasının 25.000 dolarlık hayat sigortası kaza sonucu ölümde 2 katını ödüyor: tam 50.000 dolar.",
     "Her husband's twenty-five-thousand-dollar life insurance pays double for accidental death: "
     "exactly fifty thousand dollars."),
    ("Kutuyu çöpten çıkarıp kırıyor.",
     "She pulls the box out of the trash and breaks it open."),
    ("İçinde kablo da yok, bir düzenek de.",
     "There are no wires inside, and no mechanism."),
    ("Kutu bomboş.",
     "The box is completely empty."),
    ("Telefon tekrar çalıyor.",
     "The phone rings again."),
    ("Arayan Steward.",
     "It's Steward."),
    ("Norma, ölecek kişiyi tanımayacağını söylediklerini haykırıyor.",
     "Norma screams that they told her she wouldn't know the person who'd die."),
    ("Steward ise ona kocasını gerçekten tanıyıp tanımadığını soruyor.",
     "Steward asks her whether she ever really knew her husband."),
    ("Norma için bedeli ödeyecek kişi uzak ve isimsiz bir yabancıydı; ama her yabancı bir başkasının en yakınıydı.",
     "For Norma, the person who would pay the price was a distant, nameless stranger. "
     "But every stranger was someone else's nearest and dearest."),
]

# Narration takes (indices into LINES). One take per story beat keeps the performance continuous.
TAKES = [
    list(range(0, 5)),     # cold open
    list(range(5, 11)),    # the package and the visitor
    list(range(11, 18)),   # the offer, the torn card, the call
    list(range(18, 25)),   # the package returns, dinner, Norma's dreams
    list(range(25, 31)),   # pressing the button, the hospital call
    list(range(31, 37)),   # insurance, the empty box
    list(range(37, 41)),   # Steward's call and the reveal
]

# Delivery gets more serious as the story progresses.
TAKE_MOOD = [
    "Intriguing, a quiet hook. Let the final question 'Would you press it?' hang.",
    "Curious storytelling, setting the scene.",
    "Growing unease.",
    "Tense and thoughtful; the temptation is building.",
    "Serious. 'Nothing happens.' is flat and short. The hospital news is grave, never melodramatic.",
    "Quiet, cold realization.",
    "Restrained and heavy. The last sentence is the twist: slow down slightly, small pause before "
    "'But every stranger', then land 'nearest and dearest' with calm, understated weight. No shouting.",
]
