# Smart Investment Bot

🤖 **Akıllı Yatırım Botu** - Multi-asset automated trading bot with advanced risk management and profit optimization.

## ✨ Özellikler

### 💼 Multi-Asset Trading
- **Kripto Para**: Binance API entegrasyonu ile BTC, ETH ve diğer major coins
- **Hisse Senedi**: Yahoo Finance ile US ve TR hisse senetleri
- **Forex**: Alpha Vantage ile major currency pairs

### 📈 Trading Stratejileri
- **Scalping**: 1-5 dakikalık hızlı alım-satım
- **Swing Trading**: 1-7 günlük orta vadeli pozisyonlar
- **Teknik Analiz**: RSI, MACD, Bollinger Bands, Moving Averages

### 🛡️ Risk Yönetimi
- **Otomatik Stop-Loss/Take-Profit**: Dinamik risk kontrolü
- **Position Sizing**: Sermayenin %2'si maksimum risk per trade
- **Portfolio Risk**: Toplam portföy riski %10 limiti
- **Correlation Analysis**: İlişkili varlık kontrolü

### 🎯 Profit Optimization
- **Günlük %1 Hedef**: Dinamik hedef ayarlama algoritması
- **Bileşik Kazanç**: (1.01)^gün formülü ile 
- **Hedef Başarım**: 1. ay %34.8, 2. ay %80 kazanç
- **Adaptif Hedefler**: Geride kalındığında kalan günlere dağıtım

### 🌐 Web Dashboard
- **Real-time Monitoring**: WebSocket ile canlı takip
- **Performance Charts**: Chart.js ile görsel analiz
- **Manual Trading**: Web interface üzerinden manuel işlem
- **Risk Analytics**: Gerçek zamanlı risk göstergeleri

### 🔔 Bildirimler
- **Telegram Bot**: Trading alerts ve performans raporları
- **Discord Webhook**: Rich embed notifications
- **Email Alerts**: SMTP ile email bildirimleri (opsiyonel)

## 🚀 Kurulum

### 1. Repository Clone
```bash
git clone https://github.com/selcukkurak/smart-investment-bot.git
cd smart-investment-bot
```

### 2. Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigürasyon
```bash
# Örnek dosyaları oluştur
python src/main.py setup

# Konfigürasyon dosyalarını kopyala
cp config/config.example.yaml config/config.yaml
cp .env.example .env

# API anahtarlarını ayarla
nano .env
```

### 4. API Anahtarları (.env dosyasında)
```env
# Binance API (Kripto trading için)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret

# Alpha Vantage API (Forex/Stock için)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Telegram Bot (Opsiyonel)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🎮 Kullanım

### Bot'u Başlatma
```bash
# Console mode
python src/main.py

# Web dashboard ile
python run_web.py
# Tarayıcıda: http://localhost:8000
```

### Docker ile Çalıştırma
```bash
# Docker build
docker-compose up -d

# Logs takip
docker-compose logs -f smart-investment-bot
```

## 📊 Dashboard Özellikleri

### Ana Ekran
- **Portfolio Overview**: Toplam değer, günlük/toplam kazanç
- **Performance Chart**: 7/30/90 günlük performans grafikleri
- **Active Positions**: Mevcut pozisyonlar ve P&L
- **Recent Trades**: Son işlemler tablosu

### Risk Yönetimi
- **Risk Level**: LOW/MEDIUM/HIGH/EXTREME göstergesi
- **Portfolio Risk**: Toplam portföy risk oranı
- **VaR (95%)**: Value at Risk hesaplaması
- **Risk Recommendations**: Otomatik öneriler

### Trading Interface
- **Manual Trading**: Web üzerinden manuel işlem
- **Market Opportunities**: Algoritma tarafından bulunan fırsatlar
- **Signal Generation**: Strateji sinyalleri
- **Emergency Stop**: Acil durum tüm pozisyonları kapatma

## 🔧 Konfigürasyon

### Ana Bot Ayarları
```yaml
bot:
  initial_capital: 10000.0    # Başlangıç sermayesi
  trading_mode: paper         # paper/live/backtest
  max_positions: 10           # Maksimum pozisyon sayısı
  max_risk_per_trade: 0.02    # Trade başına max risk %2
```

### Strateji Ayarları
```yaml
strategies:
  scalping:
    enabled: true
    timeframe: 5m
    rsi_oversold: 30
    rsi_overbought: 70
    stop_loss_pct: 0.005      # %0.5
    take_profit_pct: 0.01     # %1.0

  swing:
    enabled: true
    timeframe: 4h
    stop_loss_pct: 0.03       # %3
    take_profit_pct: 0.08     # %8
```

## 📈 Trading Algoritması

### Profit Calculator
```python
# Günlük %1 hedef
daily_target = 0.01

# Bileşik kazanç hesaplama
compound_profit = (1.01 ** days) - 1

# Dinamik hedef ayarlama
if current_day > 10 and achieved_profit < target:
    remaining_days = month_days - current_day
    adjusted_daily_target = (target_profit - achieved) / remaining_days
```

### Risk Management
```python
# Position size hesaplama
risk_amount = capital * max_risk_per_trade  # %2
stop_loss_distance = abs(entry_price - stop_loss)
position_size = risk_amount / stop_loss_distance

# Portfolio risk kontrolü
total_risk = sum(position_risks)
if total_risk / capital > max_portfolio_risk:  # %10
    reject_trade()
```

## 🧪 Testing

### Unit Tests
```bash
# Tüm testler
python -m pytest tests/ -v

# Specific tests
python -m pytest tests/test_profit_calculator.py -v
python -m pytest tests/test_bot.py -v
python -m pytest tests/test_strategies.py -v
```

### Integration Test
```bash
# Bot başlatma testi
python src/main.py &
sleep 10
curl http://localhost:8000/api/health
```

## 📊 Performans Metrikleri

### Hedef Kazançlar
- **1. Ay**: %34.8 toplam kazanç
- **2. Ay**: %80 toplam kazanç
- **Günlük**: %1 ortalama kazanç
- **Risk/Reward**: Minimum 1:2 oranı

### Key Performance Indicators (KPI)
- **Total Return**: Toplam kazanç yüzdesi
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: Maksimum düşüş
- **Win Rate**: Kazançlı işlem oranı
- **Profit Factor**: Toplam kazanç / Toplam zarar

## 🔧 API Entegrasyonları

### Binance API
```python
# Kripto fiyatları ve trading
binance = BinanceClient(api_key, api_secret, testnet=True)
price = await binance.get_price('BTC/USDT')
order = await binance.place_order('BTC/USDT', 'market', 'buy', 0.001)
```

### Yahoo Finance
```python
# Hisse senedi verileri
yahoo = YahooFinanceClient()
price = await yahoo.get_price('AAPL')
info = await yahoo.get_company_info('AAPL')
```

### Alpha Vantage
```python
# Forex ve fundamentals
alpha = AlphaVantageClient(api_key)
rate = await alpha.get_price('EURUSD')
indicators = await alpha.get_technical_indicators('EURUSD', 'RSI')
```

## 🛡️ Güvenlik

### API Güvenliği
- API anahtarları environment variables'da
- Rate limiting ve retry logic
- Input validation
- Error handling

### Trading Güvenliği
- Paper trading mode default
- Maximum position limits
- Automatic stop-loss
- Emergency stop functionality

## 📝 Logs ve Monitoring

### Log Dosyaları
```
logs/
├── bot.log              # Ana bot logs
├── bot_performance.log  # Performans logs
├── bot_audit.log        # Audit trail
└── bot_session_*.log    # Session logs
```

### Monitoring
- Real-time WebSocket updates
- Performance dashboards
- Risk alerts
- Trade notifications

## 🐳 Docker Deployment

### Local Development
```bash
docker-compose up -d
```

### Production
```bash
# Environment variables ayarla
cp .env.example .env
nano .env

# Production build
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

### Development Setup
```bash
# Development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Tests
python -m pytest tests/ -v --cov=src
```

### Code Style
- **Python**: PEP 8 + Black formatter
- **JavaScript**: ES6+ + Prettier
- **CSS**: BEM methodology

## 📄 License

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

## 📞 İletişim

- **GitHub Issues**: Bug reports ve feature requests
- **Email**: [EMAIL_PLACEHOLDER]
- **Discord**: [DISCORD_PLACEHOLDER]

## ⚠️ Disclaimer

Bu bot eğitim ve araştırma amaçlıdır. Gerçek para ile trading yapmadan önce:

1. **Paper trading** ile test edin
2. **Risk yönetimi** kurallarını anlayın  
3. **Piyasa risklerini** değerlendirin
4. **Yatırım danışmanı** ile görüşün

**Yatırım riski yatırımcıya aittir. Geçmiş performans gelecek performansının garantisi değildir.**