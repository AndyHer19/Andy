# 🤖 Bot de Telegram de señales cripto

Bot que vigila el mercado de criptomonedas y te manda una notificación por Telegram cuando varios indicadores técnicos coinciden en una **posible compra** o **posible venta**.

> ⚠️ **No es consejo financiero.** El bot solo te da una base de análisis; **las decisiones las tomas tú**. Los indicadores técnicos fallan con frecuencia, sobre todo en noticias o mercados muy volátiles.

## Qué analiza

En cada revisión descarga velas **cerradas** de la API pública de Binance (no necesitas cuenta ni API key) y calcula una puntuación:

| Indicador | Compra (+) | Venta (−) |
|---|---|---|
| RSI(14) | < 30: +2 · < 40: +1 | > 70: −2 · > 60: −1 |
| MACD (12,26,9) | cruce al alza: +2 · momentum alcista: +0.5 | cruce a la baja: −2 · momentum bajista: −0.5 |
| EMA50 / EMA200 | tendencia alcista: +1 · cruce dorado: +1.5 | tendencia bajista: −1 · cruce de la muerte: −1.5 |
| Bollinger (20, 2σ) | precio bajo banda inferior: +1 | precio sobre banda superior: −1 |
| Volumen | pico > 1.8× la media multiplica la puntuación ×1.25 | |

- Puntuación ≥ `SIGNAL_THRESHOLD` (por defecto 3) ⇒ 🟢 **POSIBLE COMPRA**
- Puntuación ≤ −`SIGNAL_THRESHOLD` ⇒ 🔴 **POSIBLE VENTA**
- Si no, ⚪ neutral (no se avisa).

Cada alerta incluye precio, cambio 24h, los motivos y **niveles orientativos** de stop-loss (1.5× ATR) y objetivo (3× ATR).

**Anti-spam:** solo te avisa cuando la señal cambia. Si la misma señal sigue activa, no la repite hasta que pase `COOLDOWN_HOURS`.

## Puesta en marcha

### 1. Crear el bot en Telegram
1. Abre Telegram y habla con **@BotFather**.
2. Envía `/newbot`, elige nombre y usuario.
3. Copia el **token** que te da.

### 2. Configurar
```bash
git clone <este repo> && cd Andy
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edita `.env` y pon tu `TELEGRAM_BOT_TOKEN`.

### 3. Obtener tu chat id
```bash
python main.py
```
Escribe `/start` a tu bot: te responderá con tu **chat id**. Ponlo en `TELEGRAM_CHAT_ID` dentro de `.env` y reinicia el bot. Desde ese momento **solo tu chat** puede usarlo.

### 4. Dejarlo corriendo 24/7
El bot tiene que estar encendido para avisarte. Opciones:
- **Docker** (en un VPS, Raspberry Pi, etc.):
  ```bash
  docker build -t crypto-bot .
  docker run -d --name crypto-bot --restart unless-stopped --env-file .env -v crypto-bot-data:/data crypto-bot
  ```
- **Sin Docker**: `nohup python main.py &` o un servicio `systemd`.

> Si Binance está bloqueado en tu país, la URL por defecto (`data-api.binance.vision`) suele funcionar igual porque es solo de datos públicos. Puedes cambiarla con `MARKET_API_URL`.

## Comandos

| Comando | Qué hace |
|---|---|
| `/analizar BTC` | Análisis al momento de una moneda (acepta `BTC`, `btcusdt`, `ETH/USDT`…) |
| `/resumen` | Estado de todas tus monedas, ordenadas por puntuación |
| `/lista` | Monedas vigiladas |
| `/agregar SOL` | Vigilar una moneda nueva |
| `/quitar SOL` | Dejar de vigilarla |
| `/pausar` / `/reanudar` | Pausar o reanudar las alertas automáticas |
| `/config` | Ver la configuración actual |
| `/ayuda` | Ayuda |

## Configuración (`.env`)

| Variable | Por defecto | Descripción |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Token de @BotFather (obligatorio) |
| `TELEGRAM_CHAT_ID` | — | Tu chat id (solo él puede usar el bot) |
| `SYMBOLS` | `BTCUSDT,ETHUSDT` | Monedas iniciales (luego puedes usar `/agregar`) |
| `INTERVAL` | `4h` | Temporalidad: `15m`, `1h`, `4h`, `1d`… Más larga = menos señales pero más fiables |
| `CHECK_EVERY_MINUTES` | `15` | Cada cuánto revisar |
| `SIGNAL_THRESHOLD` | `3` | Sube a 4–5 para recibir solo señales más claras |
| `COOLDOWN_HOURS` | `12` | Horas antes de repetir la misma señal |
| `MARKET_API_URL` | `https://data-api.binance.vision` | API de datos de mercado |
| `STATE_FILE` | `state.json` | Dónde guarda tu lista de monedas y últimas señales |

## Tests
```bash
python -m unittest -v
```

## Estructura
```
main.py                  # punto de entrada
crypto_bot/
  config.py              # lectura de .env
  market.py              # descarga de velas (Binance)
  indicators.py          # RSI, EMA, MACD, Bollinger, ATR
  signals.py             # motor de puntuación y señales
  state.py               # persistencia y anti-spam
  messages.py            # formato de los mensajes
  telegram_api.py        # cliente de la Bot API
  bot.py                 # comandos y bucle principal
tests/
```
