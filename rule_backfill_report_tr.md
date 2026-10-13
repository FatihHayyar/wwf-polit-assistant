# Kural tabanlı sınıflandırma — sonuç

Bugünkü Ollama uygulaması ve deney dosyaları kaldırıldı. Son push (`b20f074`) temel alınarak yalnızca kural tabanlı iyileştirmeler yeniden uygulandı. Commit veya push yapılmadı.

Dört ana kategorinin her birinde yerel **Sonstiges** var. Kategoriler, çeviriler, eş anlamlılar, eşleştirme türleri ve eşikler `app/classification/taxonomy.json` üzerinden düzenleniyor. Silinen kategoriler ve kurallar tarihsel referansları koruyarak devre dışı bırakılıyor.

Başlıkta açık konular, birleşik kelimeler ve çekimler yakalanıyor. Genel idare, siyaset, bütçe ve eğitim ifadeleri çevresel bağlantı olmadan sınıflandırma oluşturmuyor. Aynı ana kategoride belirli bir alt kategori bulunduğunda yerel Sonstiges kaldırılıyor; farklı konular birlikte etiketlenebiliyor. Bozuk HTML içeren gerçek bir belge toplu çalışmayı durdurdu; metni koruyan hata toleransı eklenerek işlem kaldığı yerden tamamlandı.

**Karışık kalite testi:** eski kurallar **40/50**, yeni kurallar **50/50**. Açık WWF örnekleri **20/20**, ilgisiz örnekler **20/20**, belirsiz/çok konulu örnekler **10/10** doğru. Beş çok konulu örneğin tamamı beklenen konuları kapsıyor. Beklentiler kaynak metinlerinden bağımsız belirlenmiştir. Bu geliştirme setindeki başarı bütün verinin anlamsal doğruluğunu kanıtlamaz. Kayıt bazında sonuçlar [kalite raporunda](rule_quality_report_tr.md).

**Doğrulama:** 90 otomatik test ve arayüz kontrolleri geçti. Paralel ve tek süreç değerlendirmesi 300 kayıtta aynı kategori, puan ve güven düzeyini verdi; bu karşılaştırmada PostgreSQL'e yazılmadı.

**Toplu uygulama tamamlandı:** dokuz veri türünde **2.951.254 kayıt** `rule-based-v7` ile sınıflandırıldı. Bağımsız salt okunur sorgu her veri türünde **0 eksik kayıt ve 0 eski sürüm sınıflandırması** doğruladı. Kaynak kayıtlar değiştirilmedi; bildirim oluşturulmadı. Ayrıntılı kapsam sayıları [rule_backfill_status.json](rule_backfill_status.json) dosyasında.

| Veri türü | Tamamlanan kayıt |
|---|---:|
| Affairs | 326.124 |
| Agendas | 423.161 |
| Meetings | 33.677 |
| Votings | 77.144 |
| Events | 916.688 |
| Documents | 909.151 |
| Texts | 226.062 |
| Groups | 8.886 |
| Interests | 30.361 |

API ve scheduler çalışır durumda değildi; yalnızca PostgreSQL konteyneri açıktı. Uygulama bir sonraki başlangıçta yeni kodu kullanacak. Yapılandırma ve yeniden hesaplama komutları [docs/configuration.md](docs/configuration.md) dosyasında.
