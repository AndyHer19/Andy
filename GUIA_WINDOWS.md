# Guía paso a paso: el bot de Binance en Windows

Tiempo aproximado: 30–45 minutos. No necesitas saber programar: solo copia y pega los comandos.

> ⚠️ Esto no es asesoramiento financiero. Sigue el orden de la guía:
> **backtest → paper → testnet → live**. No pases a dinero real sin haber probado antes.

---

## Paso 1. Instalar Python

1. Entra en <https://www.python.org/downloads/> y pulsa **Download Python 3.x**.
2. Abre el instalador descargado.
3. **MUY IMPORTANTE:** en la primera pantalla marca la casilla
   **☑ Add python.exe to PATH** (abajo del todo).
4. Pulsa **Install Now** y espera a que termine. Cierra el instalador.

**Comprobar que funciona:**
1. Pulsa la tecla **Windows**, escribe `PowerShell` y ábrelo.
2. Escribe y pulsa Enter:
   ```powershell
   python --version
   ```
3. Debe salir algo como `Python 3.13.x`.
   - Si se abre la **Microsoft Store** o sale un error, prueba con `py --version`.
     Si eso funciona, usa `py` en lugar de `python` en todos los comandos de esta guía.
   - Si ninguno funciona, reinstala Python asegurándote de marcar **Add python.exe to PATH**.

---

## Paso 2. Descargar el bot

1. Entra en <https://github.com/AndyHer19/Andy/tree/claude/que-puedes-hacer-pazln4>
   (inicia sesión en GitHub si te lo pide).
2. Pulsa el botón verde **<> Code** → **Download ZIP**.
3. Ve a tu carpeta **Descargas**, haz clic derecho sobre el ZIP → **Extraer todo...** → **Extraer**.
4. Mueve la carpeta extraída a `C:\` y cámbiale el nombre a **`BotBinance`**.
   Debe quedar así: `C:\BotBinance\binance_bot`, `C:\BotBinance\README.md`, etc.

   > Comprueba que no quede una carpeta dentro de otra (`C:\BotBinance\Andy-...\binance_bot`).
   > Si pasa, mueve el contenido de la carpeta interior directamente a `C:\BotBinance`.

---

## Paso 3. Abrir PowerShell en la carpeta del bot

1. Abre el **Explorador de archivos** y entra en `C:\BotBinance`.
2. Haz clic en la **barra de direcciones** (arriba, donde pone la ruta), escribe `powershell`
   y pulsa **Enter**.
3. Se abrirá una ventana azul/negra que empieza por `PS C:\BotBinance>`.

A partir de aquí, todos los comandos se escriben en esa ventana.

---

## Paso 4. Instalar lo que necesita el bot (solo la primera vez)

Copia y pega estos comandos **uno por uno**, pulsando Enter después de cada uno:

```powershell
python -m venv .venv
```
(crea un entorno aislado para el bot; tarda unos segundos y no muestra nada)

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
(permite activar el entorno; si pregunta, escribe `S` o `Y` y Enter)

```powershell
.\.venv\Scripts\Activate.ps1
```
Ahora la línea debe empezar por **`(.venv)`**. Eso significa que el entorno está activo.

```powershell
pip install -r requirements.txt
```
(descarga las librerías; tarda 1–2 minutos)

---

## Paso 5. Crear tu archivo de configuración

```powershell
copy .env.example .env
notepad .env
```

Se abre el Bloc de notas. Por ahora **deja `MODO=paper`** y no pongas claves.
Puedes cambiar estos valores si quieres:

| Línea | Qué significa | Valor inicial recomendado |
|---|---|---|
| `PAR` | Qué moneda opera | `BTC/USDT` |
| `TEMPORALIDAD` | Tamaño de cada vela | `15m` |
| `CANTIDAD_POR_OPERACION_USDT` | Cuánto gasta en cada compra | `20` |
| `STOP_LOSS_PCT` | Vende si cae este % | `2` |
| `TAKE_PROFIT_PCT` | Vende si sube este % | `4` |
| `PERDIDA_MAXIMA_DIARIA_USDT` | Se detiene si pierde esto en un día | `50` |

Guarda con **Ctrl + G** (o Ctrl + S) y cierra el Bloc de notas.

---

## Paso 6. Probar la estrategia con el pasado (backtest)

```powershell
python -m binance_bot.backtest --par BTC/USDT --temporalidad 1h --velas 2000
```

Verás algo así:
```
Operaciones:   37  (ganadoras 15, acierto 40.5 %)
Resultado:     +3.21 USDT
Saldo final:   1003.21 USDT (inicial 1000)
```

Prueba otras combinaciones cambiando `--temporalidad` (`15m`, `4h`) o `--sl` / `--tp`.
Si el resultado es negativo en casi todas, **la estrategia no te conviene** con esos ajustes.

---

## Paso 7. Ejecutar el bot en modo simulado (paper)

```powershell
python -m binance_bot.bot
```

Verás:
```
Bot iniciado | modo=PAPER | par=BTC/USDT | 15m | SMA 9/21
```

- El bot revisa el mercado cada 60 segundos. Puede pasar **horas** sin operar: solo compra
  cuando las medias se cruzan.
- Cuando opere verás líneas con 🟢 **COMPRA** y 🔴 **VENTA**.
- Todo queda guardado en el archivo `C:\BotBinance\bot.log`.
- Para **detenerlo**: pulsa **Ctrl + C**.

Déjalo funcionando unos días para ver cómo se comporta.

---

## Paso 8. Conectar a la red de pruebas de Binance (testnet)

Aquí el bot ya envía órdenes reales a Binance, pero con **dinero falso**.

**8.1 Crear las claves de prueba**
1. Entra en <https://testnet.binance.vision>.
2. Pulsa **Log In with GitHub** y autoriza.
3. Pulsa **Generate HMAC_SHA256 Key**, escribe una descripción (ej. `bot`) y genera.
4. Copia la **API Key** y la **Secret Key** y pégalas temporalmente en el Bloc de notas.
   ⚠️ La Secret Key **solo se muestra una vez**.

**8.2 Ponerlas en el bot**
```powershell
notepad .env
```
Cambia estas líneas (sin espacios ni comillas):
```
MODO=testnet
BINANCE_API_KEY=pega_aqui_tu_api_key
BINANCE_API_SECRET=pega_aqui_tu_secret_key
```
Guarda y cierra.

**8.3 Arrancar**
```powershell
python -m binance_bot.bot
```
Debe decir `modo=TESTNET`. La cuenta de testnet ya trae saldo falso de USDT y BTC.

> La testnet se reinicia de vez en cuando (aprox. una vez al mes) y borra saldos y claves.
> Si de repente las claves dejan de funcionar, genera otras nuevas.

---

## Paso 9. Dinero real (live) — solo cuando estés seguro

**9.1 Crear las claves en tu cuenta real de Binance**
1. Entra en <https://www.binance.com> → icono de perfil → **Gestión de API** (API Management).
2. **Crear API** → **Generada por el sistema** → ponle un nombre → completa la verificación
   (correo, SMS o autenticador).
3. Pulsa **Editar restricciones** y deja **solo**:
   - ☑ **Habilitar lectura**
   - ☑ **Habilitar trading de margen y spot** (solo spot es lo que usa el bot)
   - ☐ **Habilitar retiros → NUNCA lo actives**
4. Recomendado: en **Restricción de acceso IP** elige *Restringir a IP de confianza* y pon la IP
   de tu casa (la ves buscando "cuál es mi IP" en Google). Si tu IP cambia, tendrás que
   actualizarla.
5. Copia la API Key y la Secret Key.

**9.2 Configurar el bot**
```powershell
notepad .env
```
```
MODO=live
BINANCE_API_KEY=tu_api_key_real
BINANCE_API_SECRET=tu_secret_key_real
CONFIRMAR_LIVE=SI_ENTIENDO_EL_RIESGO
CANTIDAD_POR_OPERACION_USDT=10
```
- Necesitas tener **USDT en tu billetera Spot** de Binance (no en Fondos ni en Earn).
- Binance exige un mínimo de unos **5 USDT por orden**; usa 10 o más para ir seguro.

**9.3 Arrancar**
```powershell
python -m binance_bot.bot
```
Verás el aviso `⚠️ MODO LIVE: se operará con DINERO REAL.`

---

## Uso diario

**Arrancar el bot (forma fácil):** haz **doble clic** en `C:\BotBinance\iniciar_bot.bat`.

**Arrancar desde PowerShell:**
```powershell
cd C:\BotBinance
.\.venv\Scripts\Activate.ps1
python -m binance_bot.bot
```

**Detenerlo:** **Ctrl + C** o cerrar la ventana.

**Importante:**
- El bot **solo funciona mientras la ventana esté abierta y el PC encendido**.
- Evita que el PC se suspenda: **Configuración → Sistema → Inicio/apagado y batería →
  Pantalla y suspensión** → "Poner el dispositivo en suspensión" → **Nunca** (cuando esté enchufado).
- Si detienes el bot con una compra abierta, en testnet/live la recuerda al volver a arrancar
  (archivo `estado_testnet.json` / `estado_live.json`). **No borres esos archivos.**

---

## Problemas frecuentes

| Mensaje / problema | Solución |
|---|---|
| `python` abre la Microsoft Store | Usa `py` en vez de `python`, o reinstala Python marcando **Add to PATH** |
| `...Activate.ps1 cannot be loaded because running scripts is disabled` | Ejecuta `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y responde `S` |
| `No module named binance_bot` | No estás en `C:\BotBinance`. Ejecuta `cd C:\BotBinance` |
| `No module named ccxt` | El entorno no está activo (falta `(.venv)`). Ejecuta `.\.venv\Scripts\Activate.ps1` |
| `El modo 'testnet' necesita BINANCE_API_KEY...` | Revisa que pegaste las claves en `.env` y guardaste el archivo |
| `Invalid Api-Key ID` / `-2008` / `-2015` | Claves mal copiadas, de otro entorno (testnet vs real), sin permiso de trading o tu IP no está autorizada |
| `Timestamp for this request is outside of the recvWindow` / `-1021` | La hora del PC está desajustada: **Configuración → Hora e idioma → Fecha y hora → Sincronizar ahora** |
| `Service unavailable from a restricted location` / error 451 | Binance.com no está disponible en tu país (por ejemplo, EE. UU.). Este bot no funcionará desde ahí |
| `Saldo insuficiente para comprar` | Mete USDT en tu billetera **Spot** o baja `CANTIDAD_POR_OPERACION_USDT` |
| `Orden demasiado pequeña` | Sube `CANTIDAD_POR_OPERACION_USDT` a 10 o más |
| El archivo se guardó como `.env.txt` | En el Explorador: **Ver → Mostrar → Extensiones de nombre de archivo** y renómbralo a `.env` |
| El bot no compra nada | Es normal: solo compra cuando las medias se cruzan. Puede tardar horas |

---

## Seguridad — resumen

- 🔒 Nunca compartas tu archivo `.env` ni tus claves (ni siquiera conmigo en el chat).
- 🚫 Nunca actives **"Habilitar retiros"** en la API.
- 🧪 Prueba siempre primero en `paper` y `testnet`.
- 💸 Empieza en real con cantidades pequeñas que puedas permitirte perder.
- 🗑️ Si crees que una clave se ha filtrado, **bórrala en Binance inmediatamente** y crea otra.
