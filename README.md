# Smart Investment Bot

## Akıllı Yatırım Botu

Dünyanın her borsasında işlem yapabilen, emtia, kripto ve hisse senedi gibi çoklu varlık tiplerinde alım-satım yapan, günlük %1 kazanç hedefi olan ve dinamik kazanç hedefi ayarlama sistemi bulunan bir Python yatırım botu.

## Ana Özellikler

### 🎯 Kazanç Hedefi Sistemi
- **Günlük %1 kazanç hedefi** ana para üzerinden
- **Dinamik hedef ayarlama**: 10 günde %1 hedef tutturulamazsa, kalan günlerde eksik kazançları telafi
- **Kümülatif kazanç takibi**: Bileşik kazanç hesaplama
- **Risk yönetimi** ile günlük maksimum %2 kayıp limiti

### 💰 Çoklu Varlık Desteği
- **Hisse Senetleri**: ABD, Avrupa, Asya borsaları
- **Kriptopara**: Bitcoin, Ethereum, Altcoinler
- **Emtia**: Altın, Petrol, Gümüş
- **Forex**: Döviz çiftleri

### 📈 Teknik Analiz
- **Teknik göstergeler**: RSI, MACD, Bollinger Bands, Moving Averages
- **Çoklu zaman dilimi**: 1m, 5m, 15m, 1h, 4h, 1d
- **Volatilite analizi** ve pozisyon boyutlandırma
- **Momentum analizi**

### 🔌 API Entegrasyonları
- **Binance API**: Kripto işlemleri
- **Yahoo Finance**: Global piyasa verileri
- **Alpha Vantage**: Hisse senedi ve forex
- **Interactive Brokers**: Profesyonel trading
- **CoinGecko**: Kripto market verileri

## Kurulum

### Gereksinimler
- Python 3.8+
- pip package manager

### Adım 1: Repository'yi klonlayın
```bash
git clone https://github.com/selcukkurak/smart-investment-bot.git
cd smart-investment-bot
```

### Adım 2: Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

### Adım 3: Konfigürasyonu ayarlayın
```bash
# Environment variables dosyası oluşturun
cp .env.example .env

# API anahtarlarınızı .env dosyasına ekleyin
```

### Adım 4: Botu çalıştırın
```bash
# Demo mode
python main.py demo

# Full bot
python main.py
```

## Konfigürasyon

API anahtarlarını environment variables olarak tanımlayın:

```bash
export BINANCE_API_KEY="your_binance_api_key"
export BINANCE_SECRET_KEY="your_binance_secret_key"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"
```

## Kullanım

### Demo Mode
```bash
python main.py demo
```

### Production Mode
```bash
# Set environment to production
export ENVIRONMENT=production
python main.py
```

### Manuel Trading
```python
from src.core.bot import SmartInvestmentBot

bot = SmartInvestmentBot()
await bot.manual_trade("AAPL", "buy", 10)
```

## Proje Yapısı

```
smart-investment-bot/
├── src/
│   ├── core/
│   │   ├── bot.py                 # Ana bot sınıfı
│   │   ├── profit_calculator.py   # Kazanç hesaplama
│   │   ├── risk_manager.py        # Risk yönetimi
│   │   └── portfolio_manager.py   # Portföy yönetimi
│   ├── apis/
│   │   ├── binance_client.py      # Binance API
│   │   └── yahoo_finance_client.py # Yahoo Finance
│   ├── strategies/
│   │   ├── base_strategy.py       # Temel strateji
│   │   └── scalping_strategy.py   # Scalping stratejisi
│   ├── database/
│   │   └── models.py              # Veritabanı modelleri
│   └── utils/
│       ├── config.py              # Konfigürasyon
│       └── logger.py              # Log sistemi
├── tests/                         # Unit testler
├── requirements.txt               # Python bağımlılıkları
├── config.yaml                    # Konfigürasyon
└── main.py                        # Ana uygulama
```

## Özellikler

### 📊 Gerçek Zamanlı Monitoring
- Portfolio değeri takibi
- Günlük performans raporları
- Risk metrikleri
- Açık pozisyon takibi

### ⚡ Otomatik Trading
- Teknik analiz bazlı sinyal üretimi
- Otomatik pozisyon yönetimi
- Stop-loss ve take-profit
- Risk bazlı pozisyon boyutlandırma

### 🛡️ Risk Yönetimi
- Günlük maksimum %2 kayıp limiti
- Maksimum %5 drawdown koruması
- Pozisyon boyutu kontrolü
- Maksimum 5 eşzamanlı pozisyon

### 📈 Strateji Sistemı
- **Scalping**: Kısa vadeli hızlı kar stratejisi
- **Swing Trading**: Orta vadeli trend takip
- Çoklu zaman dilimi analizi
- Özelleştirilebilir parametreler

## Kazanç Hedefleri

### Günlük Hedef
- **%1 günlük kazanç** mevcut sermaye üzerinden
- Dinamik hedef ayarlama sistemi
- Eksik günlerin telafisi

### Aylık Projeksiyonlar
- **1. ay**: ~%34.8 (1.01^30)
- **2. ay**: ~%81.4 ((1.01^30)^2)
- **3. ay**: ~%144.7 ((1.01^30)^3)

## API Entegrasyonu

### Binance (Kripto)
```python
# Otomatik olarak yapılandırılır
# API anahtarları environment variables'dan alınır
```

### Yahoo Finance (Ücretsiz)
```python
# API anahtarı gerekmez
# Hisse senedi, forex ve emtia verileri
```

## Güvenlik

- API anahtarları environment variables olarak
- Sandbox mode test için
- Rate limiting koruması
- Şifrelenmiş konfigürasyon desteği

## Test Etme

```bash
# Unit testleri çalıştır
pytest tests/

# Belirli bir testi çalıştır
pytest tests/test_profit_calculator.py -v
```

## Docker Desteği

```bash
# Docker ile çalıştır
docker-compose up -d

# Logları takip et
docker-compose logs -f smart-bot
```

## Katkıda Bulunma

1. Bu repository'yi fork edin
2. Yeni bir feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Uyarı

⚠️ **Bu bot gerçek para ile trading yapar. Kullanmadan önce:**
- Demo mode ile test edin
- Risk yönetimi ayarlarını doğru yapılandırın
- Sadece kaybetmeyi göze alabileceğiniz miktarla başlayın
- Finansal piyasalarda işlem yapmak risk içerir

## İletişim

- GitHub Issues: Sorunlar ve öneriler için
- Documentation: [Wiki sayfası](../../wiki)

---

**Smart Investment Bot** - Akıllı yatırım kararları için AI destekli trading botu 🤖💹