# Sınırlar

Bu repodaki her şey public GitHub Actions metadata'sından ölçüldü. Bu bize gerçek ve
yeniden üretilebilir bir sayı verir — ama sert sınırları da var. Başlık sayısını
alıntılamadan önce bunları okuyun.

## Diyemeyeceklerimiz

**Rerun sonrası yeşil ≠ kod doğru.**
Failure'ın o koşuda commit'ten kaynaklanmadığı anlamına gelir. Yalnızca belirli
koşullarda ortaya çıkan gerçek bir bug hâlâ olabilir.

**Bu bir AI-etkisi çalışması değil.**
Hangi koşuların AI ile yazıldığını bilmiyoruz ve failure'ları (ya da iyileşmeleri)
AI'a atfetmiyoruz. Kodu kim yazarsa yazsın recovery döngüsü zaman alıyor.

**Nedensellik yok.**
Ne olduğunu ölçtük, neden olduğunu değil. Yeşile dönen rerun'lar genelde flaky test,
network veya environment sorunu demektir — ama biz yalnızca run metadata'sı
görüyoruz, log içeriği görmediğimiz için kök nedeni bu veri setinden teyit edemeyiz.

## Ölçüm sınırları

**Seçim yanlılığı (attempt bazlı ~%75).**
Geliştiriciler *flaky olduğundan şüphelendikleri* koşuları yeniden çalıştırır. ~%75,
"geliştirici rerun yapmayı seçti" koşuluna bağlıdır — rastgele bir kırmızı koşunun
iyileşme olasılığı değildir.

**Attempt collapse.**
GitHub API, run başına tek kayıt döner ve `run_attempt` güncel değeri gösterir. Ara
attempt'lerin sonuçları toplu olarak görünmez; bu yüzden attempt #1'i tümüyle değil,
rastgele örneklemle doğruluyoruz.

**Pencere ve limit.**
Veri 90 güne kadar (2026) kapsar. O pencerede 6.000'den fazla koşusu olan repolarda
en yeni 6.000 koşu limiti uygulanır; yoğun repolarda pencere kısalır. Sonuçlar anlık
görüntüdür, trend değildir.

**Repo seçimi.**
GitHub Actions kullanan 32 aktif OSS repo seçtik. Tüm repoların rastgele örneği
değiller; repo bazlı sonuçlar geniş dağılım gösterir (%0–77).

**Episode sınırı.**
Aynı `(workflow, SHA)` koşularını tek episode sayıyoruz. Çok sonra görünen aynı-SHA
koşusu (ör. günler sonra yeniden tetiklenen workflow) yine sayılır; P90 yeşile dönme
süresinin uzun olmasının nedeni budur.

## Dürüst çerçeve

> "GitHub'ın başarısız ilk denemede yeniden çalıştırıldığını kaydettiği koşuların
> ~%75'i yeşile döndü — aynı commit, kod değişikliği yok." — ölçüldü, örneklemle
> doğrulandı, 2026 public CI anlık görüntüsü. Senin rerun'unun çalışacağını ya da
> kodun doğru olduğunu söylemez.
