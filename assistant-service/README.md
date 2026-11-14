# Akademik sohbet — sunucu sürümü (v3)

## Durum

Kod ve arayüz entegrasyonu hazırdır. Bu paket bir barındırma hesabı açmaz, API anahtarı içermez ve ücretli model erişimini kendiliğinden başlatmaz. `CHAT_ENABLED=false`, günlük kota `0` ve sitedeki `content/assistant-service.json` dosyasının `endpoint` değeri boşken üretken model kapalıdır. Kaynak rehberi üretken model olarak gösterilmez. Eski Qwen 0.6B tarayıcı modeli yeni arayüzde yüklenmez.

## Nasıl çalışır?

Ziyaretçi onay verince yalnızca mevcut soru ve sınırlı yakın konuşma geçmişi sunucuya gider. Sunucu, sitenin yayımlanmış ve sürüm numarası alınmış kaynaklarını kendisi seçer. İstemcinin gönderdiği model adı, kaynak veya sistem talimatı kabul edilmez. Yanıt; açıklama, isteğe bağlı tek devam sorusu ve kaynak kimlikleriyle döner. Kaynak kimlikleri gerçek kayıtlara eşlenir; uydurma kimlik içeren yanıt gösterilmez. Bu kontrol, bir kaynağın iddiayı anlamsal olarak desteklediğini tek başına garanti etmez.

Normal konuşmada 80–180 kelimelik, doğal Türkçe/İngilizce yanıt hedeflenir. Genel yöntem önerisi kişisel onaydan ayrılır. Belirsiz görevler, destek kararları, kabul ve randevular uydurulmaz. Model seçim ayarı `OPENAI_MODEL` sunucudadır; varsayılan `gpt-5.4` canlı yanıt değerlendirmesi yapılmadan kalite garantisi sayılmaz.

## Kurulum

1. Önce GitHub Pages güncellemesini yayımlayın. `assets/assistant-context.json` oluşmalıdır.
2. Yetkilendirilmiş Vercel projesinde Root Directory olarak `assistant-service` seçin. Node.js 22 kullanılır. `npm run build`, yalnızca sabit site adresinden açık bilgi paketini indirir; eksik paketle dağıtımı durdurur.
3. Vercel ortam değişkenlerine `OPENAI_API_KEY`, `OPENAI_MODEL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, rastgele en az 32 karakterlik `QUOTA_SECRET` ekleyin. Bunları GitHub'a, tarayıcı dosyasına veya sohbete koymayın.
4. Sahibinin onayladığı **istek sayısını** `CHAT_DAILY_LIMIT` olarak belirleyin. Bu dolar bütçesi değildir. Ayrıca model sağlayıcısında harcama/uyarı ayarları yapın. Kullanıcı onayı olmadan faturalandırmayı açmayın.
5. Sınırlı deneme için `CHAT_ENABLED=true` ile hizmeti açın; gerçek yanıtları aşağıdaki değerlendirmeden geçirin.
6. Ancak kabul edilebilir sonuçlardan sonra `content/assistant-service.json` içindeki `endpoint` alanına kendi servisinizin `https://.../api/chat` adresini yazıp siteyi yeniden yayımlayın.

## Koruma ve mahremiyet

CORS yalnızca mevcut site alan adına izin verir; CORS kimlik doğrulama değildir ve bir istemcinin Origin taklit etmesini engellemez. Model çağrısından önce Redis üzerinde atomik global günlük kota ve dakika başına istemci kotası ayrılır. Depo çalışmıyorsa sistem çağrıyı kapatır. Kota kimlikleri günlük HMAC özetidir; mesajlar veya açık IP adresleri Redis'e yazılmaz. İstek sayısı limiti, kullanılan token miktarına göre değişen maliyet için mutlak parasal sınır değildir. Canlı kullanımda ek WAF/bot önlemleri ve sağlayıcı maliyet denetimi önerilir.

Uygulama sohbetleri günlüğe yazmaz. `store:false` kullanılır; bu, model sağlayıcısı ve barındırma hizmetinin tüm işletim/güvenlik kayıtlarını ortadan kaldırdığı iddiası değildir. Arayüz gönderim öncesinde bu ayrımı gösterir. Temizleme, sekmedeki geçmişi siler; önceden gönderilmiş veriyi geri almaz.

Sunucu; 2.000 karakterlik kullanıcı mesajını, en çok 15 mesajı, 20.000 karakterlik geçmişi, en çok 6 kaynak parçasını ve 2.200 çıktı tokenını sınırlar. Ücretli çağrı otomatik yeniden denenmez. Hata mesajları sağlayıcı yanıtını veya anahtarı sızdırmaz.

## Test ve gerçek kalite değerlendirmesi

- `node --test test/*.test.mjs`: doğrulama, kaynak seçimi, bağlam değişimi, kotanın çağrıyı engellemesi, kaynaksız/uydurma referanslı yanıtın reddi. Model yanıtı deneme verisidir.
- `python tests/assistant_v3_browser.py` (depo kökünde): Türkçe/İngilizce, üç ekran genişliği, gönderim/onay, bağlam, hata/yeniden deneme, sıfırlama, zararlı HTML metni ve model indirmeme. Kısıtlı yerel ortamda `--offline` desteklenir. Sunucu taşıma yanıtı mock'tur.
- `node evaluate.mjs`: varsayılan olarak **SKIPPED**. Gerçek sağlayıcı testi, yalnızca yetkilendirilmiş `EVAL_ENDPOINT` ve açık `RUN_LIVE_EVAL=1` ile çalışır; ücret/kota tüketir. Hiçbir gerçek model sonucu bu pakette varmış gibi raporlanmaz.

`evaluate.mjs` araştırma fikri geliştirme, 7. sınıf devam sorusu, 3501 ekibi, Yeşim'in iki projede yer alması, belirsiz Ahmet sorusu, bilinmeyen teknik görev, fon durumu ve kişiyi taklit etme taleplerini kapsar. İnsan değerlendirici Türkçe akıcılığı, soruya doğrudan yanıt, bağlam sürekliliği, kaynak desteği ve uydurma bilgi ölçütlerini kontrol etmelidir. Koda ait testlerin geçmesi, bu değerlendirmenin yerine geçmez.

## Resmî teknik dayanaklar

- OpenAI Responses: https://developers.openai.com/api/reference/resources/responses/methods/create
- Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Model: https://developers.openai.com/api/docs/models/gpt-5.4
- Veri kontrolleri: https://developers.openai.com/api/docs/guides/your-data
- Vercel Node: https://vercel.com/docs/functions/runtimes/node-js
- Ortam değişkenleri: https://vercel.com/docs/environment-variables
- Kalıcı kota REST API: https://upstash.com/docs/redis/features/restapi
