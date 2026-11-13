# Andy — Bot de trading para Binance

Bot en Python que se conecta a Binance (spot) y **compra y vende automáticamente** siguiendo
una estrategia de **cruce de medias móviles**, con stop loss, take profit y límite de pérdida diaria.

> ⚠️ **Aviso:** esto no es asesoramiento financiero. Ningún bot garantiza ganancias.
> Empieza siempre en modo `paper` o `testnet` y nunca inviertas dinero que no puedas perder.

## Cómo funciona

| Regla | Acción |
|---|---|
| La media rápida (9) cruza por **encima** de la lenta (21) | **Compra** `CANTIDAD_POR_OPERACION_USDT` |
| La media rápida cruza por **debajo** de la lenta | **Vende** toda la posición |
| El precio cae un `STOP_LOSS_PCT` % desde la compra | Vende (limita la pérdida) |
| El precio sube un `TAKE_PROFIT_PCT` % desde la compra | Vende (asegura la ganancia) |
| Las pérdidas del día superan `PERDIDA_MAXIMA_DIARIA_USDT` | No abre más operaciones hasta mañana |

Solo usa velas ya cerradas y abre como máximo una posición a la vez.

## Modos

| Modo | Precios | Órdenes | ¿Claves? |
|---|---|---|---|
| `paper` | Reales | Simuladas en tu ordenador | No |
| `testnet` | Red de pruebas de Binance | Reales, pero con dinero falso | Sí (de testnet) |
| `live` | Reales | **Reales, con tu dinero** | Sí + confirmación |

## Instalación

```bash
git clone https://github.com/andyher19/andy.git
cd andy
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # En Windows: copy .env.example .env
```

Edita `.env` con tu configuración.

## Uso

**1. Prueba la estrategia con datos históricos (backtest):**
```bash
python -m binance_bot.backtest --par BTC/USDT --temporalidad 1h --velas 2000
```

**2. Ejecuta el bot en modo simulado** (`MODO=paper` en `.env`):
```bash
python -m binance_bot.bot
```
Para detenerlo pulsa `Ctrl + C`. Todo queda registrado en `bot.log`.

**3. Testnet:** crea claves en <https://testnet.binance.vision> (inicia sesión con GitHub),
ponlas en `.env` con `MODO=testnet` y vuelve a ejecutar el bot.

**4. Live (dinero real):** solo cuando lleves semanas probando y entiendas los resultados.
- Crea las claves en Binance → *Gestión de API* con **solo** “Habilitar trading spot”.
- **Nunca** actives “Habilitar retiros”. Si puedes, restringe las claves a la IP de tu servidor.
- Pon `MODO=live` y `CONFIRMAR_LIVE=SI_ENTIENDO_EL_RIESGO`.
- Empieza con cantidades pequeñas. El mínimo de Binance por orden es de unos 5 USDT.

## Seguridad

- El archivo `.env` contiene tus claves: está en `.gitignore`, **no lo subas nunca a GitHub**
  ni lo compartas con nadie.
- En `testnet` y `live` el bot guarda su posición abierta en `estado_<modo>.json` para
  recuperarla si se reinicia. No borres ese archivo con una posición abierta.

## Tests

```bash
python -m pytest -q
```

## Estructura

```
binance_bot/
  config.py      # lectura y validación del .env
  estrategia.py  # cruce de medias móviles
  riesgo.py      # stop loss, take profit, límite diario
  exchange.py    # conexión a Binance (paper / testnet / live)
  bot.py         # bucle principal
  backtest.py    # pruebas con datos históricos
tests/
```
