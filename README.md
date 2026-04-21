# UI Auditor with Playwright

Modern, Playwright tabanlı bir arayüz denetim aracı. Bir siteyi hem masaüstü hem de mobil görünümde dolaşır, kırık bağlantıları ve görselleri tespit eder, mobil düzen sorunlarını işaretler ve sonuçları ekran görüntüleriyle birlikte tek bir HTML raporda sunar.

## İçindekiler

1. [Özet](#özet)
2. [Ne Yapar?](#ne-yapar)
3. [Sistem Gereksinimleri](#sistem-gereksinimleri)
4. [Kurulum](#kurulum)
5. [Kullanım](#kullanım)
6. [Parametreler](#parametreler)
7. [Çıktı Yapısı](#çıktı-yapısı)
8. [Proje Yapısı](#proje-yapısı)
9. [Stealth Modu](#stealth-modu)
10. [İnsan Benzeri Davranış Simülasyonu](#insan-benzeri-davranış-simülasyonu)
11. [Access Denied ve Loading Durumu](#access-denied-ve-loading-durumu)
12. [Sorun Giderme](#sorun-giderme)
13. [Yasal Uyarı ve Kullanım Koşulları](#yasal-uyarı-ve-kullanım-koşulları)
14. [Lisans](#lisans)

## Özet

```bash
# 1. Depoyu klonla
git clone https://github.com/Cin42720/UiAuditorwithPlaywrite.git

# 2. Proje klasörüne gir
cd UiAuditorwithPlaywrite/ui-auditor

# 3. Bağımlılıkları kur
npm install

# 4. Chromium'u indir
npm run install:browsers

# 5. Demo raporunu üret
npm run audit:demo
```

Demo çıktıları:

- [HTML rapor](output/ui-auditor/demo-report/index.html)
- [JSON sonuç](output/ui-auditor/demo-report/audit-result.json)
- [Rapor önizleme görseli](output/ui-auditor/demo-report/report-preview.png)

## Ne Yapar?

- Bir hedef URL'den başlayarak aynı origin altında kalan sayfaları otomatik keşfeder ve belirlenen sayıda sayfayı denetler.
- Her sayfa için iki ayrı görünüm üretir:
  - Masaüstü: `1440x980` viewport
  - Mobil: `iPhone 13` emülasyonu
- Kırık bağlantıları tespit eder:
  - Sayfadaki her `<a href>` bağlantısını önce `HEAD`, gerekirse `GET` isteğiyle kontrol eder.
  - `HTTP 400+` dönen bağlantıları listeler.
- Yüklenmeyen görselleri bulur:
  - Tarayıcının `complete` ve `naturalWidth` değerlerini kullanır.
  - Başarısız görsel isteklerini ayrıca yakalar.
- Mobil düzen sorunlarını raporlar:
  - Buton / link / `role="button"` elemanları arasındaki belirgin örtüşmeleri tespit eder.
  - Viewport'tan taşan yatay kaydırma sorunlarını işaretler.
- Görsel HTML rapor üretir:
  - Masaüstü ve mobil ekran görüntülerini yan yana gösterir.
  - Sorunları kategorilere ayırır.
- Erişim kısıtı tespiti yapar:
  - `401`, `403`, `429`, `access denied`, `blocked`, `captcha` gibi durumları ayrı uyarı olarak gösterir.
  - Böyle bir durumda yanıltıcı olmamak için düzen testlerini atlar.
- Stealth desteklidir:
  - `playwright-extra` ve `puppeteer-extra-plugin-stealth` ile bot olarak algılanma riskini azaltmaya çalışır.
- İnsan benzeri gezinme davranışını simüle eder:
  - Fare hareketleri
  - Yumuşak kaydırma
  - Rastgele bekleme süresi

## Sistem Gereksinimleri

- İşletim sistemi: Windows 10/11, macOS 12+, Linux
- Node.js: `18.0.0` veya üstü
- npm: `8.0.0` veya üstü
- Yaklaşık 500 MB boş disk alanı
- İnternet erişimi

Kullanılan temel paketler:

- `playwright`
- `playwright-extra`
- `puppeteer-extra-plugin-stealth`

Bağımlılıkların güncel listesi için [ui-auditor/package.json](ui-auditor/package.json) dosyasına bakabilirsiniz.

## Kurulum

```bash
git clone https://github.com/Cin42720/UiAuditorwithPlaywrite.git
cd UiAuditorwithPlaywrite/ui-auditor
npm install
npm run install:browsers
```

İlk `npm run install:browsers` çalıştırması Playwright için Chromium indirir. Bu işlem bağlantı hızına göre birkaç dakika sürebilir.

## Kullanım

### Demo raporu üretmek

```bash
cd ui-auditor
npm run audit:demo
```

Bu komut yerel demo siteyi ayağa kaldırır, denetimi çalıştırır ve şu klasöre rapor yazar:

```text
output/ui-auditor/demo-report/
```

### Gerçek bir siteyi denetlemek

```bash
cd ui-auditor
npm run audit -- https://example.com
```

Belirli sayıda sayfa taramak için:

```bash
npm run audit -- https://example.com --max-pages 10
```

Farklı bir çıktı klasörü kullanmak için:

```bash
npm run audit -- https://example.com --output ./my-report
```

Demo sunucusunu tek başına çalıştırmak isterseniz:

```bash
cd ui-auditor
npm run serve:demo
```

## Parametreler

| Parametre | Açıklama | Varsayılan |
|---|---|---|
| `<url>` | Denetimin başlayacağı tam URL | Zorunlu |
| `--max-pages <n>` | Denetlenecek maksimum sayfa sayısı | `5` |
| `--output <path>` | Çıktı klasörü | `output/ui-auditor/latest` |

Araç doğrudan Node ile de çalıştırılabilir:

```bash
cd ui-auditor
node src/audit-site.mjs https://example.com --max-pages 3
```

## Çıktı Yapısı

Varsayılan çıktı yapısı:

```text
output/ui-auditor/latest/
├── index.html
├── audit-result.json
└── screenshots/
```

Dosyalar:

- `index.html`: tarayıcıda açılabilen görsel rapor
- `audit-result.json`: makine tarafından işlenebilir ham çıktı
- `screenshots/`: masaüstü ve mobil ekran görüntüleri

Örnek JSON özeti:

```json
{
  "summary": {
    "pagesAudited": 2,
    "checkedLinks": 103,
    "brokenLinks": 0,
    "brokenImages": 0,
    "mobileIssues": 3,
    "blockedPages": 0,
    "warningCount": 0
  }
}
```

## Proje Yapısı

```text
UiAuditorwithPlaywrite/
├── README.md
├── LICENSE
├── output/
│   └── ui-auditor/
└── ui-auditor/
    ├── demo-site/
    ├── src/
    │   ├── audit-site.mjs
    │   ├── demo-server.mjs
    │   ├── report-template.mjs
    │   ├── run-demo-audit.mjs
    │   └── static-server.mjs
    ├── package.json
    └── package-lock.json
```

## Stealth Modu

Varsayılan headless Playwright kullanımı bazı sitelerde kolayca tespit edilebilir. UI Auditor bunu azaltmak için ek önlemler alır:

- `playwright-extra` kullanır
- `puppeteer-extra-plugin-stealth` ile Playwright imzasını gizlemeye çalışır
- daha gerçekçi kullanıcı ajanı ve tarayıcı davranışı üretir
- istemci ipuçları ve dil bilgilerini tutarlı gönderir

Amaç, kendi sitenizde veya açık izinli ortamlarda yapılan meşru denetimlerin yanlışlıkla engellenmesini azaltmaktır.

## İnsan Benzeri Davranış Simülasyonu

Araç sayfa yüklendikten sonra küçük bir gezinme rutini çalıştırır:

1. Rastgele fare hareketleri yapar
2. Sayfada aşağı ve yukarı yumuşak kaydırma uygular
3. Kısa ve rastgele bekleme süresi ekler

Bunun iki faydası vardır:

- davranışsal bot filtrelerine karşı daha doğal görünür
- lazy-load görsellerin gerçekten yüklenmesini sağlar

## Access Denied ve Loading Durumu

Bazı siteler Playwright veya headless tarayıcı kullanan istekleri bot gibi algılayabilir. Böyle durumlarda:

- `403`, `Access denied`, `blocked`, `captcha` gibi cevaplar alınabilir
- mobil görünüm yalnızca `Loading...` ekranında kalabilir
- gerçek sayfa yerine koruma ekranı gösterilebilir

UI Auditor böyle bir durumda:

- sayfayı `Access restricted` veya `Stalled loading state` uyarısı ile işaretler
- ekran görüntülerini almaya devam eder
- ancak düzen bulgularını raporlamayı atlar

Böylece yanlış pozitif mobil overlap sonuçları üretmez.

## Sorun Giderme

**`Executable doesn't exist` hatası**

Playwright tarayıcısı kurulu değildir:

```bash
cd ui-auditor
npm run install:browsers
```

**Tüm sayfalar `Access restricted` görünüyor**

Muhtemel nedenler:

- site anti-bot koruması kullanıyordur
- IP adresiniz kısıtlanmıştır
- çerez / oturum gereklidir

**Denetim çok yavaş**

Çözüm:

- `--max-pages` değerini düşürün
- sadece gerekli sayfaları denetleyin

**Rapor yarım kaldı**

Çıktı klasörünü temizleyip yeniden çalıştırın:

```bash
cd ui-auditor
npm run audit -- https://example.com --output ./clean-report
```

## Yasal Uyarı ve Kullanım Koşulları

UI Auditor yalnızca:

- kendi sahip olduğunuz sitelerde
- ya da açık ve yazılı izin aldığınız ortamlarda

kullanılmalıdır.

Bu araç:

- yetkisiz erişim
- güvenlik testi
- veri kazıma
- bot koruması aşma

amacıyla tasarlanmamıştır.

Özellikle dikkat edilmesi gerekenler:

- `stealth` ve insan davranışı simülasyonu bir koruma aşma aracı değildir
- kişisel veri içeren ekran görüntülerini paylaşmadan önce gözden geçirin
- hedef sitenin hizmet şartlarını ve yerel mevzuatı dikkate alın
- bir site sahibi taramayı durdurmanızı isterse denetimi durdurun

Bu projeyi kullanan kişi, kullanım sorumluluğunu kendisi üstlenir.

## Lisans

Bu proje MIT lisansı ile paylaşılmıştır. Ayrıntı için [LICENSE](LICENSE) dosyasına bakın.
