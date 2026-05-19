# UI Auditor with Playwright

Python Playwright tabanlı modern bir arayüz denetim aracı. Bir hedef siteyi hem masaüstü hem de mobil görünümde dolaşır, kırık bağlantıları ve yüklenmeyen görselleri bulur, mobil düzen sorunlarını işaretler ve sonuçları ekran görüntüleriyle birlikte HTML/JSON rapor olarak üretir.

Bu sürüm Node.js yapısından çıkarılıp Python proje yapısına taşınmıştır. Mevcut işlevler korunmuştur: site keşfi, link kontrolü, görsel kontrolü, mobil çakışma/taşma analizi, iPhone 13 emülasyonu, desktop/mobile ekran görüntüsü, HTML raporu, demo site, erişim kısıtı uyarıları ve stealth benzeri tarayıcı ayarları.

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

```powershell
# 1. Depoyu klonla
git clone https://github.com/Cin42720/UiAuditorwithPlaywright.git

# 2. Proje klasörüne gir
cd UiAuditorwithPlaywright

# 3. Sanal ortam oluştur ve etkinleştir
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4. Python bağımlılıklarını kur
python -m pip install -r requirements.txt

# 5. Playwright Chromium tarayıcısını indir
python -m playwright install chromium

# 6. Demo raporunu üret
python -m ui_auditor demo
```

macOS/Linux için sanal ortam etkinleştirme komutu:

```bash
source .venv/bin/activate
```

Demo çıktıları varsayılan olarak şu klasöre yazılır:

- `output/ui-auditor/demo-report/index.html`
- `output/ui-auditor/demo-report/audit-result.json`
- `output/ui-auditor/demo-report/screenshots/`

## Ne Yapar?

- Bir hedef URL'den başlayarak aynı origin altında kalan sayfaları otomatik keşfeder ve belirlenen sayıda sayfayı denetler.
- Her sayfa için iki ayrı görünüm üretir:
  - Masaüstü: `1440x980` viewport
  - Mobil: Playwright `iPhone 13` emülasyonu
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
- Stealth benzeri destek içerir:
  - Gerçekçi user-agent, dil, timezone ve client hint başlıkları kullanır.
  - Playwright otomasyon izlerini azaltmak için context init script uygular.
- İnsan benzeri gezinme davranışını simüle eder:
  - Fare hareketleri
  - Yumuşak kaydırma
  - Rastgele bekleme süresi

## Sistem Gereksinimleri

- İşletim sistemi: Windows 10/11, macOS 12+, Linux
- Python: `3.10` veya üstü
- Yaklaşık 500 MB boş disk alanı
- İnternet erişimi

Kullanılan temel paket:

- `playwright`

Bağımlılıklar için [requirements.txt](requirements.txt) ve [pyproject.toml](pyproject.toml) dosyalarına bakabilirsiniz.

## Kurulum

```powershell
git clone https://github.com/Cin42720/UiAuditorwithPlaywright.git
cd UiAuditorwithPlaywright
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

`python -m playwright install chromium` komutu Playwright için Chromium indirir. Bu işlem bağlantı hızına göre birkaç dakika sürebilir.

Projeyi komut satırı aracı olarak kurmak isterseniz:

```powershell
python -m pip install -e .
ui-auditor demo
```

## Kullanım

### Demo raporu üretmek

```powershell
python -m ui_auditor demo
```

Bu komut paket içindeki demo siteyi yerel olarak başlatır, denetimi çalıştırır ve raporu şu klasöre yazar:

```text
output/ui-auditor/demo-report/
```

### Gerçek bir siteyi denetlemek

```powershell
python -m ui_auditor audit https://example.com
```

Kısa kullanım da desteklenir:

```powershell
python -m ui_auditor https://example.com
```

Belirli sayıda sayfa taramak için:

```powershell
python -m ui_auditor audit https://example.com --max-pages 10
```

Farklı bir çıktı klasörü kullanmak için:

```powershell
python -m ui_auditor audit https://example.com --output ./my-report
```

Demo sunucusunu tek başına çalıştırmak isterseniz:

```powershell
python -m ui_auditor serve-demo
```

## Parametreler

| Parametre | Açıklama | Varsayılan |
|---|---|---|
| `<url>` | Denetimin başlayacağı tam URL | Zorunlu |
| `--max-pages <n>` | Denetlenecek maksimum sayfa sayısı | `5` |
| `--output <path>` | Çıktı klasörü | `output/ui-auditor/latest` |
| `--port <n>` | Demo sunucu portu | `4173` |

Python API ile kullanmak için:

```python
from ui_auditor import audit_site

report = audit_site(
    target_url="https://example.com",
    max_pages=3,
    output_dir="output/ui-auditor/latest",
)
print(report["summary"])
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
UiAuditorwithPlaywright/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── ui_auditor/
│   ├── __init__.py
│   ├── __main__.py
│   ├── auditor.py
│   ├── cli.py
│   ├── report.py
│   ├── static_server.py
│   └── demo_site/
│       ├── index.html
│       ├── about.html
│       ├── styles.css
│       └── assets/
└── output/
    └── ui-auditor/
```

## Stealth Modu

Varsayılan headless Playwright kullanımı bazı sitelerde kolayca tespit edilebilir. UI Auditor bunu azaltmak için Python tarafında ek önlemler alır:

- gerçekçi user-agent kullanır
- `Accept-Language`, client hints, locale ve timezone değerlerini tutarlı ayarlar
- `navigator.webdriver`, `navigator.languages`, `navigator.plugins` gibi yaygın otomasyon sinyallerini context init script ile yumuşatır
- insan benzeri fare ve kaydırma davranışı üretir

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

```powershell
python -m playwright install chromium
```

**`No module named playwright` hatası**

Python bağımlılıkları kurulmamıştır:

```powershell
python -m pip install -r requirements.txt
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

```powershell
python -m ui_auditor audit https://example.com --output ./clean-report
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

- stealth ve insan davranışı simülasyonu bir koruma aşma aracı değildir
- kişisel veri içeren ekran görüntülerini paylaşmadan önce gözden geçirin
- hedef sitenin hizmet şartlarını ve yerel mevzuatı dikkate alın
- bir site sahibi taramayı durdurmanızı isterse denetimi durdurun

Bu projeyi kullanan kişi, kullanım sorumluluğunu kendisi üstlenir.

## Lisans

Bu proje MIT lisansı ile paylaşılmıştır. Ayrıntı için [LICENSE](LICENSE) dosyasına bakın.
