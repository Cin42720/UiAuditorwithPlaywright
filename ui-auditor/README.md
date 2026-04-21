# UI Auditor

Modern, Playwright tabanlı bir arayüz denetim aracı. Bir siteyi hem desktop hem de mobil görünümde dolaşır, kırık bağlantıları ve görselleri tespit eder, mobil layout sorunlarını işaretler ve sonuçları yan yana ekran görüntüleriyle birlikte tek bir HTML raporda sunar.

## İçindekiler

1. [Özet](#özet)
2. [Ne Yapar?](#ne-yapar)
3. [Sistem Gereksinimleri](#sistem-gereksinimleri)
4. [Kurulum](#kurulum)
5. [Kullanım](#kullanım)
6. [Parametreler](#parametreler)
7. [Çıktı Yapısı](#çıktı-yapısı)
8. [Stealth Modu](#stealth-modu)
9. [İnsan Benzeri Davranış Simülasyonu](#i̇nsan-benzeri-davranış-simülasyonu)
10. [Access Denied ve Loading Durumu](#access-denied-ve-loading-durumu)
11. [Sorun Giderme](#sorun-giderme)
12. [Yasal Uyarı ve Kullanım Koşulları](#yasal-uyarı-ve-kullanım-koşulları)

## Özet

```bash
# 1. Bağımlılıkları kur
npm install

# 2. Chromium'u indir (ilk kurulumda bir kez)
npm run install:browsers

# 3. Bir siteyi audit et
npm run audit -- https://example.com

# 4. Raporu tarayıcıda aç
# output/ui-auditor/latest/index.html
```

## Ne Yapar?

- Bir hedef URL'den başlayarak aynı origin altında kalan sayfaları otomatik keşfeder ve belirlenen sayıda sayfayı denetler (BFS, varsayılan 5 sayfa).
- Her sayfa için iki paralel denetim yapar:
  - **Desktop**: 1440x980 viewport, tam sayfa ekran görüntüsü
  - **Mobil**: iPhone 13 emülasyonu, tam sayfa ekran görüntüsü
- **Kırık bağlantılar**: Sayfadaki her `<a href>`'yi önce `HEAD`, gerekirse `GET` ile kontrol eder; HTTP 400+ dönenleri listeler.
- **Yüklenmeyen görseller**: Tarayıcının `complete` ve `naturalWidth` değerlerini ve `requestfailed` olaylarını kullanarak render edilemeyen `<img>` kaynaklarını toplar.
- **Mobil layout sorunları**:
  - Buton / link / `role=button` elemanları arasında 80 px²'den büyük örtüşmeler
  - Viewport'tan taşan yatay scroll (`document.documentElement.scrollWidth > innerWidth + 8`)
- **HTML rapor**: Desktop ve mobil ekran görüntülerini yan yana gösteren, sorunları kategoriye ayrılmış modern bir `index.html` üretir.
- **Anti-bot / erişim kısıtı tespiti**: 401 / 403 / 429 veya tipik engelleme metinlerini (`access denied`, `cloudflare`, `checking your browser`, vb.) görürse sayfayı `Access restricted` olarak işaretler ve layout testlerini atlar (yanılsamalı sonuçları engellemek için).
- **Stealth modu**: `playwright-extra` + `puppeteer-extra-plugin-stealth` ile Playwright/headless imzasını gizler, gerçekçi UA / locale / timezone / client hints ekler.
- **İnsan benzeri davranış simülasyonu**: Rastgele fare hareketi, yumuşak kaydırma ve 2-3 saniye rastgele bekleme ile meşru kullanıcı izi bırakır, lazy-load görsellerin de yüklenmesini sağlar.

## Sistem Gereksinimleri

- **İşletim sistemi**: Windows 10/11, macOS 12+, Linux (Ubuntu 20.04+ veya dengi)
- **Node.js**: 18.0+ (LTS önerilir; Playwright 1.59 bunu gerektirir)
- **npm**: 8.0+
- **Disk**: Chromium binary'si dahil yaklaşık 500 MB boş alan
- **Bellek**: Denetim sırasında 1 GB+ RAM; sayfa başına ~150 MB
- **Ağ**: Hedef sitelere çıkış izni

Kütüphane listesi için [requirements.txt](./requirements.txt) dosyasına bakınız.

## Kurulum

```bash
# Depoyu klonla (veya zip olarak indir)
git clone <repo-url>
cd ui-auditor

# Node bağımlılıkları
npm install

# Playwright'ın kullanacağı Chromium binary'sini indir
npm run install:browsers
```

İlk `install:browsers` çalıştırması 150-250 MB indirme gerektirir ve internete bağlı olarak 1-3 dakika sürebilir. Aynı makinede Playwright'ı zaten kullandıysanız binary tekrar indirilmez.

## Kullanım

### Demo raporu

Dahili demo sitesi üzerinde aracın çıktısını görmek için:

```bash
npm run audit:demo
```

Demo raporu şu dosyaya yazılır:

```
output/ui-auditor/demo-report/index.html
```

Demo sunucusunu ayrı bir terminalde elle ayağa kaldırmak istersen:

```bash
npm run serve:demo
```

### Gerçek bir siteyi denetlemek

```bash
npm run audit -- https://example.com
```

Varsayılan çıktılar şu klasöre yazılır:

```
output/ui-auditor/latest/
├── index.html          # Görüntülenen rapor
├── audit-result.json   # Makine okunabilir ham sonuç
└── screenshots/        # Desktop ve mobil ekran görüntüleri
```

Birden fazla sayfayı taramak için:

```bash
npm run audit -- https://example.com --max-pages 10
```

Farklı bir çıktı klasörü kullanmak için:

```bash
npm run audit -- https://example.com --output ./my-report
```

## Parametreler

| Parametre | Açıklama | Varsayılan |
|---|---|---|
| `<url>` (konum) | Denetim başlangıcı olan mutlak URL (http/https). | **zorunlu** |
| `--max-pages <n>` | Aynı origin altında denetlenecek maksimum sayfa sayısı (BFS). | `5` |
| `--output <path>` | Raporların yazılacağı klasör. | `../output/ui-auditor/latest` |

Araç ayrıca doğrudan Node ile de çalıştırılabilir:

```bash
node src/audit-site.mjs https://example.com --max-pages 3
```

## Çıktı Yapısı

- **`index.html`** — Özet metrikler, her sayfa için desktop/mobile ekran görüntüleri ve sorun listesi.
- **`audit-result.json`** — `summary`, `pages` ve uyarı tiplerini içeren yapılandırılmış sonuç. CI/CD'de bu dosyayı ayrıştırarak regresyon kapısı kurulabilir.
- **`screenshots/page-XX-desktop.png` / `page-XX-mobile.png`** — Tam sayfa PNG'ler, sırayla numaralandırılır.

`audit-result.json` içindeki temel alanlar:

```json
{
  "summary": {
    "pagesAudited": 2,
    "checkedLinks": 103,
    "brokenLinks": 0,
    "brokenImages": 0,
    "mobileIssues": 101,
    "blockedPages": 0,
    "warningCount": 0
  },
  "pages": [ ... ]
}
```

## Stealth Modu

Varsayılan Playwright + headless Chromium kombinasyonu WAF / bot koruması olan sitelerde kolayca yakalanır:

- `navigator.webdriver === true`
- `HeadlessChrome` User-Agent'ı
- `--enable-automation` başlatma flag'i
- Boş / tutarsız `navigator.plugins`, `navigator.permissions`, `WebGL` bilgileri

UI Auditor bu imzayı gizlemek için `playwright-extra` üzerine `puppeteer-extra-plugin-stealth` kullanır. Buna ek olarak:

- **User-Agent**: Gerçekçi Chrome 124 UA'sı (Windows x64).
- **Locale & timezone**: `tr-TR` / `Europe/Istanbul` — tutarlı bir kullanıcı kimliği.
- **Client hints**: Her isteğe `Accept-Language`, `Sec-CH-UA`, `Sec-CH-UA-Mobile`, `Sec-CH-UA-Platform`, `Upgrade-Insecure-Requests` başlıkları eklenir. Mobil context için `Sec-CH-UA-Mobile: ?1` ve `Sec-CH-UA-Platform: "iOS"` override edilir.
- **Launch flag'leri**: `--disable-blink-features=AutomationControlled`, `--disable-features=IsolateOrigins,site-per-process`, `--no-sandbox`.
- **Challenge bekleme**: Sayfa yükleme sonrasında `waitForChallenge` yardımcısı, "Just a moment", "Checking your browser", "Verifying you are human" veya "Attention required" gibi Cloudflare / DataDome benzeri geçici ekranların kapanmasını 8 saniyeye kadar bekler. Challenge çözüldüyse denetim gerçek sayfa üzerinden devam eder; çözülmezse mevcut "Access restricted" mantığı devreye girer.

Stealth modunun amacı kendi veya yazılı izin verilmiş sitelerinizin **meşru denetimlerinin yanlış pozitif olarak bloklanmasını önlemektir**; bir sitenin bot korumasını bilerek atlatmak için tasarlanmamıştır.

## İnsan Benzeri Davranış Simülasyonu

Stealth fingerprint maskelemesi yeterli olmayabilir — bazı WAF'lar (Cloudflare Bot Management, DataDome, PerimeterX/HUMAN, Akamai Bot Manager) **davranışsal sinyalleri** de ölçer: fare entropisi, scroll ivmesi, olay zamanlaması.

UI Auditor bu nedenle sayfa yükledikten sonra küçük bir "insanileştirme" rutini çalıştırır (`humanize` yardımcısı):

1. **Rastgele 3 fare hareketi** — `page.mouse.move(x, y, { steps: 12-24 })` ile viewport içerisinde farklı koordinatlara pürüzsüz (ara noktalı) hareket; her hareket sonrasında 120-280 ms jitter.
2. **Yumuşak kaydırma** — Sayfa sonuna kadar kademeli `scrollBy({ behavior: "smooth" })`, ardından en tepeye `scrollTo({ behavior: "smooth" })`. Bu adım ayrıca **lazy-load görsellerin gerçekten yüklenmesini sağlar**, böylece `brokenImages` tespiti daha güvenilir olur.
3. **Rastgele 2-3 saniye bekleme** — Sabit bir gecikme yerine `Math.random() * 1000 + 2000` ms. Tahmin edilebilir trafik parmak izi bırakmamak için.

Tüm rutin `try/catch` ile sarmalanmıştır: fare veya scroll çalıştırılamayan bloklu sayfalarda sessizce atlar, denetim yarıda kalmaz.

Sayfa başına yaklaşık +5-7 saniye ekler. `--max-pages` değerini büyük tuttuysanız toplam süreye dikkat edin.

## Access Denied ve Loading Durumu

Bazı siteler Playwright veya headless tarayıcı kullanan istekleri (stealth modu devredeyken bile) bot gibi algılayıp `403`, `Access denied`, `blocked`, `captcha` gibi cevaplar döndürebilir.

UI Auditor bu durumda:

- Sayfayı `Access restricted` uyarısı ile işaretler
- Desktop ve mobil ekran görüntüsü almaya devam eder
- Layout bulgularını raporlamayı atlar, çünkü o noktada görülen ekran gerçek sayfa değildir

Benzer şekilde mobil sayfa uzun süre `Loading...` ekranında kalırsa araç bunu `Stalled loading state` olarak not eder ve mobil layout sonuçlarını atlar.

Bu sayede **gerçek UI problemleri ile anti-bot / erişim problemleri birbirine karışmaz**.

## Sorun Giderme

**`Error: Executable doesn't exist at ...\chromium-XXXX\chrome.exe`**
Playwright browser binary'si kurulu değil. `npm run install:browsers` komutunu çalıştırın.

**Tüm sayfalar `Access restricted` olarak işaretleniyor**
Hedef site stealth + davranış simülasyonuna rağmen Playwright'ı tespit ediyor. Yapılabilecekler:
- Farklı bir çıkış IP'si deneyin (site sizin IP'nizi blokluyor olabilir).
- `launchPersistentContext` ile bir tarayıcı profili oluşturup siteyi bir kez elle ziyaret edin, çerezleri yeniden kullanın.
- Çok agresif korumalarda `camoufox` veya `patchright` gibi daha sert stealth forkları daha etkili olabilir.

**Denetim çok yavaş**
- `--max-pages` değerini düşürün.
- Tek sayfa denetimi yaklaşık 15-25 saniye (davranış simülasyonu dahil) sürer; bu beklenen oranlıktır.

**`ENOENT: audit-result.json` veya bozuk rapor**
Denetim sırasında süreç kesildiyse çıktı yarım kalabilir. `output/ui-auditor/latest/` klasörünü silip yeniden çalıştırın.

**Timeout hataları**
`audit-site.mjs` içindeki `timeout: 25000` değerlerini yükseltebilirsiniz. Çok yavaş yüklenen sitelerde 45000'e çıkarmak mantıklı.

## Yasal Uyarı ve Kullanım Koşulları

UI Auditor yalnızca **kendi sahip olduğunuz** ya da **denetim için açık yazılı izniniz bulunan** siteler üzerinde kullanılmalıdır. Araç, tasarım kalitesini ve erişilebilirliği iyileştirmeyi hedefleyen defansif/kaliteci bir UI denetim aracıdır; yetkisiz erişim, veri kazıma, güvenlik testi veya yük testi için tasarlanmamıştır.

Kullanmadan önce aşağıdakileri değerlendirmek kullanıcının sorumluluğundadır:

- Hedef sitenin **hizmet şartları (Terms of Service)** ve `robots.txt` dosyası
- Yürürlükteki veri koruma ve bilgisayar suçları mevzuatı (Türkiye için 6698 sayılı KVKK ve 5237 sayılı TCK md. 243-245; AB için GDPR; ABD için CFAA gibi)
- Site operatörünün rate-limit, bot tespit ve erişim politikaları

Özellikle dikkat edilmesi gerekenler:

- **Stealth modu ve insan davranış simülasyonu birer "kilit kırma" aracı değildir.** Amaçları, meşru denetimlerin yanlış pozitif olarak bloklanmasını azaltmaktır. Hedef sitenin bot korumasını bilerek devre dışı bırakmak, CAPTCHA'yı atlamak veya erişim kısıtlamalarını aşmak için kullanılmamalıdır.
- **Kişisel veri işlemeyin.** Alınan ekran görüntüleri ve metin örnekleri (`textSample`) üye profilleri, e-posta adresleri veya başka kişisel veriler içerebilir. Bu çıktılar `output/` klasörü altında yerel olarak tutulur; başkalarıyla paylaşmadan önce gözden geçiriniz.
- **İzinsiz üçlü taraf sitelerinde kullanım kullanıcının kendi riski ve sorumluluğundadır.** Proje sahipleri bu aracı izinsiz audit / tarama amacıyla kullanımından doğan hiçbir hukuki, mali veya idari sorumluluğu kabul etmez.
- Araç bir site sahibinden **"bu taramayı durdurun" talebi** alırsa taramayı derhal durdurun ve ilgili siteyi bundan sonra hedef almayın.
- **Rate limiting'e uyun.** Varsayılan sayfa başına ~5-7 sn gecikme bunun içindir; `--max-pages` değerini yükseltirken toplam yükün sitenin operasyonel limitlerini aşmadığından emin olun.

Bu projeyi klonlayan, kullanan veya türetilen çalışmalar üreten herkes bu şartları kabul etmiş sayılır. Şartlara uyulmamasından doğan her türlü sonucun sorumluluğu münhasıran kullanıcıya aittir.
