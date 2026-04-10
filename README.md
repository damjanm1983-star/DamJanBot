# DamJanBot 🤖📈

**Автоматизиран Trading Bot за Binance Futures**  
*Создаден од Dame и Jan | 2026*

---

## 📋 Што е ова?

**DamJanBot** е автоматизиран систем за тргување со криптовалути кој ги поврзува **TradingView** стратегиите со **Binance Futures** преку webhook alerts. Ботот работи во **paper trading (dry-run)** режим - симулира тргување без реален ризик.

---

## 🏗️ Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   TradingView   │────▶│   VPS Webhook    │────▶│   Trading Bot   │
│  (Pine Script)  │     │  (Nginx + Python)│     │  (Dry-Run Engine)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                           │
                              ▼                           ▼
                       ┌──────────────┐          ┌──────────────┐
                       │  Dashboard   │          │  Binance API │
                       │  (Real-time) │          │  (Simulated) │
                       └──────────────┘          └──────────────┘
```

---

## 🔧 Компоненти

### 1. **TradingView Pine Script** (`BTCUSDT_V7_5_webhook.pine`)
- Стратегија за BTCUSDT на 5m timeframe
- Генерира BUY/SELL сигнали базирани на техничка анализа
- Испраќа webhook alerts во реално време
- Користи `open` цена за следната свеќа (next bar execution)

```pinescript
alert('{"action":"buy","symbol":"' + syminfo.ticker + '","price":' + str.tostring(open) + '}', alert.freq_once_per_bar)
```

### 2. **Webhook Handler** (`webhook_handler.py`)
- Flask сервер на порт 8000
- Прима JSON alerts од TradingView
- Валидација на сигнали
- Пренесува до dry-run engine

**Endpoint:** `POST http://5.9.248.66/webhook`

### 3. **Dry-Run Engine** (`dry_run_engine.py`)
- Симулира тргување без реални пари
- Прати позиции: FLAT → LONG / SHORT
- Пресметува P&L (profit/loss)
- Заштита од дупликат сигнали

**Параметри:**
- Баланс: $1000 (paper)
- Позиција: 50% од баланс ($500)
- Маргина: 30% (~3.3x leverage)
- Симбол: BTCUSDT

### 4. **Dashboard** (`trading_bot_server.py`)
- Real-time веб интерфејс на порт 8080
- Покажува тековна позиција, P&L, историја
- Auto-refresh секои 5 секунди

**URL:** http://5.9.248.66:8080

### 5. **Binance API Client** (`binance_api_client.py`)
- Интеграција со Binance Futures API
- Читање на цени, баланс, позиции
- Подготвен за live trading (сега disabled)

### 6. **Vibe-Trading Integration** (NEW! 🎉)
- **AI-powered finance toolkit** со 64 specialized skills
- **Backtest engines** со statistical validation (Monte Carlo, Bootstrap, Walk-Forward)
- **Technical analysis skills**: candlestick, Elliott wave, Ichimoku, SMC, harmonic patterns
- **Risk analysis**: VaR/CVaR, stress testing, tail risk
- **MCP server** за интеграција со OpenClaw
- **Wrapper script**: `vibe-trading-mcp-wrapper.sh`

**Инсталација:**
```bash
# Веќе инсталирано во venv
source venv/bin/activate
vibe-trading --skills  # Листај ги сите 64 skills
```

**Корисни skills за твојата стратегија:**
- `technical-basic` - EMA/ADX/RSI/BB/OBV (споредба со V7.5)
- `candlestick` - 15 candlestick patterns
- `backtest-diagnose` - Дијагностицирање на стратегии
- `pattern_recognition` - Chart patterns (H&S, double top, etc.)
- `risk-analysis` - VaR/CVaR, Monte Carlo simulation

---

## 📁 Структура на проектот

```
trading_bot/
├── README.md                    # Овој фајл
├── SETUP_GUIDE.md              # Детален setup guide
├── config.py                   # Конфигурација
├── trading_bot_server.py       # Dashboard сервер
├── webhook_handler.py          # Webhook примач
├── dry_run_engine.py           # Симулациски engine
├── binance_api_client.py       # Binance API wrapper
├── position_reader.py          # Читач на позиции
├── start_webhook_server.py     # Стартер за webhook
├── test_webhook_integration.py # Тестови
│
├── Pine Script стратегии:
├── BTCUSDT_V7_5_webhook.pine   # Главна стратегија (V7.5)
├── BTCUSDT_V7_4_webhook.pine   # Стара верзија (V7.4)
├── BTCUSDT_V7_4_Final.pine     # Финална верзија
├── BTCUSDT_Clean.pine          # Чиста верзија
├── BTCUSDT_5m_V7_2_Complete.pine
├── pine_script_v7_2_alerts.pine
├── pine_script_alerts_addon.pine
├── pine_script_alerts_fix.pine
│
├── tests/                      # Unit тестови
│   └── test_dry_run_engine.py
│
├── run_dashboard.sh            # Старт скрипта
├── restart_dashboard.sh        # Рестарт скрипта
├── restart_with_fix.sh         # Рестарт со фикс
├── restart_with_price_fix.sh   # Рестарт со цена фикс
├── restart_dashboard_v2.sh     # Рестарт v2
├── run_tests.sh                # Тест скрипта
│
├── Backup & Restore:
├── backup_openclaw.sh          # Комплетен backup на целиот OpenClaw
├── push_backup_to_github.sh    # Push backup на GitHub
├── vibe-trading-mcp-wrapper.sh # Vibe-Trading MCP wrapper
│
└── venv/                       # Python виртуелна средина
    └── (venv/ е исклучен од git)
```

---

## 🚀 Како работи?

### Flow:
1. **TradingView** генерира сигнал (BUY/SELL)
2. **Webhook** го прима JSON alert-от
3. **Engine** процесира сигналот:
   - Проверува дали е валиден
   - Проверува дали веќе сме во таа позиција
   - Пресметува количина и цена
   - Ажурира состојба
4. **Dashboard** прикажува новата состојба

### Пример на сигнал:
```json
{
  "action": "buy",
  "symbol": "BTCUSDT",
  "price": 72139.50
}
```

### Позициска заштита:
- Веќе LONG + BUY сигнал = **игнорира** (веке сме купени)
- Веќе LONG + SELL сигнал = **затвора LONG**, отвора **SHORT**
- Веќе SHORT + SELL сигнал = **игнорира**
- Веќе SHORT + BUY сигнал = **затвора SHORT**, отвора **LONG**

---

## ⚙️ Конфигурација

### `config.py`:
```python
PAPER_MODE = True              # Симулација (не реални пари)
SYMBOL = "BTCUSDT"             # Тргувачки пар
TIMEFRAME = "5m"               # Timeframe
INITIAL_BALANCE = 1000.0       # Почетен баланс
POSITION_SIZE_PERCENT = 50     # % од баланс по позиција
MARGIN_PERCENT = 30            # Маргина %
```

---

## 🖥️ Systemd Services

Ботот работи како сервис на VPS:

```bash
# Провери статус
sudo systemctl status trading-bot
sudo systemctl status openclaw-gateway

# Логови
tail -f /tmp/trading_bot.log
tail -f /tmp/webhook_server.log
```

---

## 🔒 Безбедност

- ✅ **Dry-run mode** - нема реални пари на ризик
- ✅ **Private GitHub repo** - кодот е приватен
- ✅ **SSH keys** - безбеден пристап до GitHub
- ✅ **Nginx reverse proxy** - заштита на webhook

---

## 📊 Dashboard

**URL:** http://5.9.248.66:8080

Покажува:
- 🎯 Тековна позиција (LONG/SHORT/FLAT)
- 💰 Тековен баланс и P&L
- 📈 Количина и entry цена
- 🕐 Историја на трговии
- ⚡ Real-time refresh

---

## 🧪 Тестирање

```bash
# Пушти ги тестовите
cd /home/dame/.openclaw/workspace/trading_bot
./run_tests.sh

# Тест webhook
python3 test_webhook_integration.py
```

---

## 📝 Историја на развој

| Датум | Што направивме |
|-------|---------------|
| 2026-04-09 | Почеток на проектот, Pine Script стратегии |
| 2026-04-09 | Webhook handler и dry-run engine |
| 2026-04-09 | Dashboard со real-time приказ |
| 2026-04-09 | Nginx конфигурација |
| 2026-04-10 | Systemd services за auto-restart |
| 2026-04-10 | GitHub push со SSH клуч |
| 2026-04-10 | Синхронизација со TradingView позиција |
| 2026-04-10 | Ажурирано на V7.5 стратегија со open price execution |
| 2026-04-10 | Поправена индентација во Pine Script (if блокови) |
| 2026-04-10 | Комплетен backup/restore систем креиран |
| 2026-04-10 | **Vibe-Trading интеграција** - 64 finance skills инсталирани |
| 2026-04-10 | Анализа на `technical-basic` skill (споредба со V7.5) |

---

## 📊 Тековен Статус (2026-04-10)

| Параметар | Вредност |
|-----------|----------|
| **Стратегија** | V7.5 Webhook (работи) |
| **Позиција** | 🟢 LONG |
| **Симбол** | BTCUSDT |
| **Timeframe** | 5m |
| **Алерти** | ✅ Наместени и активни |
| **Последен сигнал** | BUY |
| **Мод** | Paper Trading (dry-run) |

## 🎯 Следни чекори

- [ ] Чекање на SELL сигнал за тест на position flip
- [ ] Telegram нотификации за трговии
- [ ] Подобрена стратегија со повеќе индикатори
- [ ] Live trading (кога ќе бидеме сигурни)

---

## 👥 Автори

**Dame & Jan** | 2026

*"Тргување со стратегија, не со емоции"* 📈

---

## 📞 Линкови

- **Dashboard:** http://5.9.248.66:8080
- **Webhook:** http://5.9.248.66/webhook
- **GitHub:** https://github.com/damjanm1983-star/DamJanBot
