# Módulo OpenClaw — guía paso a paso

Esta guía lleva desde **cero** hasta **probar que el agente (LLM + OpenClaw) llama al backend** y registra un movimiento en PostgreSQL. No asume nada instalado ni configurado: cada paso dice qué escribir, qué tenés que ver como resultado y qué hacer si no lo ves.

> **Principio del proyecto:** el agente interpreta, el backend decide. OpenClaw nunca toca la base de datos; solo llama a las 5 tools del contrato (`docs/tools.md`) a través de un servidor MCP que reenvía los pedidos al backend.

> **Estado de verificación (leer):** los pasos de instalación, configuración y las pruebas de las Capas 1 y 2 (backend y servidor MCP) se pueden comprobar de forma independiente. Las **Capas 3 y 4** (que el LLM responda y que la cadena completa llegue al backend) dependen de que OpenClaw pueda usar el modelo en Windows, y hasta ahora estaba bloqueado por el problema descrito en el Paso 18 y por la cuota del modelo. Si una capa falla, esta guía indica en cuál.

---

## 0. Cómo leer esta guía

- Todos los comandos son de **PowerShell de Windows**, salvo los que dicen "en Ubuntu (WSL)".
- **Pegá un comando a la vez.** Si pegás varios juntos pueden pegarse (`cd ..Get-ChildItem`) y fallar.
- Los textos entre `<` y `>` son para que los reemplaces (por ejemplo `<tu clave>`). **No los dejes literales.**
- Cada paso termina con **Verificación** (qué tenés que ver) y, si hace falta, **Si falla**.
- **Nunca pegues claves, contraseñas ni tokens** en chats, issues ni commits.

### Reglas de oro (leelas antes de empezar)

1. **No vuelvas a correr `openclaw onboard`** una vez completado. Reconfigurar se hace con `openclaw config ...`.
2. **No borres ni edites a mano** la carpeta `openclaw\.openclaw\` ni sus bases `.sqlite`. Es el estado del agente.
3. **No commitees** `.env`, `.openclaw\` ni `.venv\`. Ya están en `openclaw\.gitignore`.
4. En cada terminal nueva que uses para OpenClaw, primero activá el entorno del proyecto (**Paso 8**). Sin eso, los comandos apuntan a otra configuración.

---

## 1. Mapa de lo que vas a levantar

```text
Vos (chat en el dashboard de OpenClaw)
        │
        ▼
OpenClaw (gateway, puerto 18789)  ──►  LLM (Gemini u otro, vía API)
        │  tools
        ▼
Servidor MCP  openclaw/tools-mcp/server.py   (solo reenvía, sin reglas de negocio)
        │  HTTP + JWT
        ▼
Backend FastAPI  /tools/*   (puerto 8000)   ──►  PostgreSQL (puerto 5432, en WSL)
```

Vas a tener **3 terminales abiertas**: una con el backend (uvicorn), una con el gateway de OpenClaw y una para comandos. PostgreSQL corre en segundo plano dentro de WSL.

---

## 2. Requisitos previos

Verificá cada uno. Si algo no coincide, instalalo antes de seguir.

| Requisito | Comando | Qué tenés que ver |
|---|---|---|
| Windows 10/11 | `winver` | Windows 10 (2004 o posterior) o 11 |
| Git | `git --version` | `git version 2.x` |
| Node.js | `node -v` | `v24.16` o superior, o `v26.1` o superior |
| npm | `npm -v` | cualquier versión (anotala, se usa en el Paso 6) |
| Python | `python --version` | `Python 3.10` o superior |
| WSL2 | `wsl --status` | "Versión predeterminada: 2" |
| Clave de API de un LLM | — | Para Gemini: clave de Google AI Studio |

**Si falla:**
- Node: instalá la versión LTS actual desde nodejs.org y **abrí una terminal nueva**.
- WSL: en una PowerShell **como administrador** ejecutá `wsl --install -d Ubuntu`, reiniciá la PC y completá la creación de usuario de Ubuntu cuando se abra por primera vez.
- Si ves el prompt `(base)` de conda, es normal; solo asegurate de que `python --version` muestre 3.10+.

---

## 3. Obtener el proyecto y su estructura

```powershell
git clone <url-del-repositorio> TP_FINAL
cd TP_FINAL
```

Estructura que tiene que existir (las carpetas `.venv`, `.openclaw` y el archivo `.env` se crean más adelante):

```text
TP_FINAL/
├── README.md
├── backend/
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── alembic/
│   └── app/
│       ├── main.py  database.py  security.py  seed.py
│       ├── models/  schemas/
│       └── routers/   accounts.py  auth.py  transactions.py  tools.py
├── database/
├── docs/
│   └── tools.md
├── frontend/
└── openclaw/
    ├── README.md                ← esta guía
    ├── .env.example
    ├── .gitignore
    ├── start.ps1                ← levanta el gateway
    ├── llm.patch.json5          ← configuración genérica del LLM
    ├── openclaw.patch.json5     ← workspace + tools + servidor MCP
    ├── scripts/
    │   ├── load-env.ps1  use-project.ps1  probe-models.ps1
    ├── tools-mcp/
    │   ├── server.py  requirements.txt
    └── workspace/
        ├── AGENTS.md  SOUL.md  IDENTITY.md  USER.md  TOOLS.md  HEARTBEAT.md
        └── skills/finanzas/SKILL.md
```

**Verificación:** ejecutá `Get-ChildItem openclaw -Force | Select-Object Name`. Tienen que aparecer, como mínimo, `start.ps1`, `llm.patch.json5`, `openclaw.patch.json5`, `scripts`, `tools-mcp` y `workspace`.

**Importante:** no tiene que existir `workspace\BOOTSTRAP.md`. Si existe, borralo: es un archivo de "primer arranque" que hace que el agente te pregunte quién es en vez de comportarse como asistente de finanzas.
```powershell
Remove-Item openclaw\workspace\BOOTSTRAP.md -ErrorAction SilentlyContinue
```

---

# PARTE A — Backend y base de datos

El agente necesita un backend funcionando para que "llamar al backend" tenga sentido. Si ya lo tenés andando con el usuario y las cuentas de prueba, saltá a la **Parte B**.

## 4. PostgreSQL en WSL

### 4.1 Instalarlo (una sola vez)

Abrí Ubuntu (escribí `wsl` en PowerShell). Dentro de Ubuntu:

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start
```

Creá el usuario y la base. Elegí una contraseña **solo con letras y números** (si tiene `@`, `#`, `:`, `/` o `%` rompe la URL de conexión):

```bash
sudo -u postgres psql -c "CREATE USER finanzas WITH PASSWORD 'CambiarEstaClave123';"
sudo -u postgres psql -c "CREATE DATABASE finanzas_db OWNER finanzas;"
```

**Verificación:** cada comando responde `CREATE ROLE` y `CREATE DATABASE`. Salí de Ubuntu con `exit`.

### 4.2 Encenderlo (cada vez que reinicies la PC o cierre WSL)

WSL se apaga cuando está inactivo y se lleva PostgreSQL con él. Desde PowerShell:

```powershell
wsl -u root service postgresql start
```

**Verificación** (desde Windows):
```powershell
Test-NetConnection localhost -Port 5432
```
Tiene que decir `TcpTestSucceeded : True`.

**Si falla:** si dice `False`, repetí el comando de encendido. Si tenés también PostgreSQL instalado en Windows, ambos compiten por el puerto 5432: apagá uno.

## 5. Backend

### 5.1 Entorno virtual e instalación

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Si falla** por scripts deshabilitados:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
(solo afecta a esta ventana) y repetí `.\venv\Scripts\Activate.ps1`.

### 5.2 Variables del backend (`backend\.env`)

```powershell
Copy-Item .env.example .env
notepad .env
```

Completá **exactamente** estas dos (el backend lee solo estas; revisá `.env.example` por si agrega otras):

```text
DATABASE_URL=postgresql+psycopg2://finanzas:CambiarEstaClave123@localhost:5432/finanzas_db
JWT_SECRET_KEY=<valor generado abajo>
```

Reglas del formato: una sola línea, **sin comillas, sin espacios alrededor del `=`, sin `<` `>`**. Para generar `JWT_SECRET_KEY`:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```
Copiá el resultado en el `.env` (no lo compartas).

> Si tu driver es `psycopg` v3 en lugar de `psycopg2`, el prefijo es `postgresql+psycopg://`. Mirá cuál figura en `requirements.txt`.

**Verificación:** el siguiente comando muestra el nombre de las variables y oculta los valores:
```powershell
(Get-Content .env) -replace '=.*','=<oculto>'
```
Tienen que aparecer `DATABASE_URL=<oculto>` y `JWT_SECRET_KEY=<oculto>`.

**Si falla más adelante con `Could not parse SQLAlchemy URL`:** la línea `DATABASE_URL` tiene un carácter inválido (casi siempre una contraseña con símbolos, un espacio, comillas o un `#`). Corregila.

### 5.3 Tablas y categorías

Con PostgreSQL encendido (Paso 4.2) y el venv activo, desde `backend\`:

```powershell
alembic upgrade head
```
**Verificación:** termina sin error y menciona la migración `create_initial_tables`.

```powershell
python -m app.seed
```
**Verificación:** imprime `Categorias cargadas correctamente`. Crea Alimentacion, Transporte, Servicios, Vivienda, Salud, Educacion, Entretenimiento, Compras, Otros (gastos) y Sueldo, Honorarios, Inversiones, Otros (ingresos).

### 5.4 Levantar el backend (terminal 1, la dejás abierta)

```powershell
uvicorn app.main:app --reload
```
**Verificación:** ves `Uvicorn running on http://127.0.0.1:8000`. En el navegador, `http://localhost:8000/docs` muestra los endpoints, y **tienen que aparecer 5 bajo `/tools`**: `POST /tools/expense`, `POST /tools/income`, `GET /tools/balance`, `GET /tools/transactions`, `GET /tools/expenses-by-category`.

**Si falla:**
- `DATABASE_URL no esta configurada` / `JWT_SECRET_KEY no esta configurada`: el `.env` no está en `backend\` o le falta esa variable.
- `NameError: agent` o `No module named 'app.routers.agent'`: `main.py` todavía referencia el router viejo. Debe importar `from app.routers.tools import router as tools_router` y registrar `app.include_router(tools_router)`. Además, `routers\agent.py` tiene que estar borrado.
- No aparece `/tools` en `/docs`: falta registrar el router o el servidor no recargó. Cortá con Ctrl+C y levantalo de nuevo.

### 5.5 Usuario de prueba y cuentas (terminal 2, nueva)

Este usuario es el que usará el agente. Anotá el email y la contraseña: van a ir también en `openclaw\.env` (Paso 9).

```powershell
cd "<ruta>\TP_FINAL"
$base = "http://localhost:8000"
$cred = @{ email = "agente@finanzas.dev"; password = "UnaClaveDePrueba123" } | ConvertTo-Json
Invoke-RestMethod -Method Post "$base/auth/register" -ContentType "application/json" -Body $cred
```
**Verificación:** devuelve `id` y `email`. Si responde `409 El email ya esta registrado`, el usuario ya existe: usá su contraseña real o registrá otro email.

Iniciá sesión y creá 3 cuentas:
```powershell
$login = Invoke-RestMethod -Method Post "$base/auth/login" -ContentType "application/json" -Body $cred
$h = @{ Authorization = "Bearer $($login.access_token)" }
```
```powershell
$cuentas = @(
  @{ name = "Efectivo";      type = "CASH";   currency = "ARS"; initial_balance = 50000 },
  @{ name = "Mercado Pago";  type = "WALLET"; currency = "ARS"; initial_balance = 0 },
  @{ name = "Banco Nacion";  type = "BANK";   currency = "ARS"; initial_balance = 200000 }
)
foreach ($c in $cuentas) { Invoke-RestMethod -Method Post "$base/accounts" -Headers $h -ContentType "application/json" -Body ($c | ConvertTo-Json) | Out-Null }
Invoke-RestMethod "$base/accounts" -Headers $h | Select-Object id, name, type, initial_balance
```
**Verificación:** lista las tres cuentas. Los valores de `type` válidos son solo `CASH`, `BANK` y `WALLET`.

---

# PARTE B — OpenClaw

## 6. Instalar OpenClaw

La versión con la que se está trabajando en el proyecto es **2026.11.4**. Para reproducir el mismo comportamiento, instalá esa versión.

Primero mirá tu versión de npm:
```powershell
npm -v
```

- Si es **12 o 11.16 o superior**:
  ```powershell
  npm install -g openclaw@2026.11.4 --allow-scripts=openclaw
  ```
- Si es **11.15 o inferior**:
  ```powershell
  npm install -g openclaw@2026.11.4
  ```

(Podés instalar `openclaw@latest` en lugar de la versión fija, pero entonces textos y comportamientos pueden diferir de esta guía.)

**Verificación:**
```powershell
openclaw --version
```
Tiene que mostrar `OpenClaw 2026.11.4`.

**Si falla (`openclaw` no se reconoce):** casi siempre es el PATH. Cerrá y abrí la terminal. Si sigue, ejecutá `npm prefix -g` y asegurate de que esa carpeta esté en la variable de entorno `Path` de Windows.

## 7. Configurar las variables del módulo (`openclaw\.env`)

```powershell
cd "<ruta>\TP_FINAL\openclaw"
Copy-Item .env.example .env
notepad .env
```

Completá cada línea (una por variable, sin comillas):

```text
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=<tu clave de API>
LLM_MODEL=
BACKEND_URL=http://localhost:8000
AGENT_USER_EMAIL=agente@finanzas.dev
AGENT_USER_PASSWORD=UnaClaveDePrueba123
```

| Variable | Qué es |
|---|---|
| `LLM_BASE_URL` | Dirección de la API compatible con OpenAI del proveedor elegido. |
| `LLM_API_KEY` | La clave de ese proveedor. |
| `LLM_MODEL` | Id del modelo. **Lo dejás vacío ahora**; se completa en el Paso 10. |
| `BACKEND_URL` | Dónde corre el backend. |
| `AGENT_USER_EMAIL`, `AGENT_USER_PASSWORD` | El usuario de prueba que registraste en el Paso 5.5. **Tienen que ser idénticos.** |

Otras URL para `LLM_BASE_URL`: OpenAI `https://api.openai.com/v1`, OpenRouter `https://openrouter.ai/api/v1`, Ollama local `http://localhost:11434/v1`.

> **Privacidad:** el plan gratuito de Gemini puede usar lo que enviás para mejorar los productos de Google (revisá los términos vigentes). Durante el desarrollo usá solo datos de prueba.

## 8. Activar el entorno del proyecto (cada terminal nueva)

```powershell
cd "<ruta>\TP_FINAL\openclaw"
. .\scripts\use-project.ps1
```

El **punto + espacio** del principio es obligatorio: ejecuta el script *dentro* de tu terminal para que las variables queden activas. Sin el punto no sirve.

Qué hace: define `OPENCLAW_STATE_DIR`, `OPENCLAW_CONFIG_PATH` y `OPENCLAW_WORKSPACE_DIR` apuntando a esta carpeta del proyecto (así OpenClaw no usa la configuración de `C:\home\.openclaw`) y carga tu `.env`. Solo imprime **nombres** de variables, nunca valores.

**Verificación:**
```powershell
$env:OPENCLAW_CONFIG_PATH
```
Tiene que terminar en `...\TP_FINAL\openclaw\.openclaw\openclaw.json`.

**Si falla:**
- "la ejecución de scripts está deshabilitada": `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y repetí.
- Dice `no hay .env`: el archivo no está en `openclaw\`.
- Editaste el `.env` después de activar: las variables ya cargadas **no se pisan**. Abrí una terminal nueva y repetí este paso.

## 9. Onboarding (una sola vez)

Con el entorno activo (Paso 8):

```powershell
openclaw onboard
```

Respuestas usadas en el proyecto (los textos pueden variar levemente entre versiones):

| Pregunta | Respuesta |
|---|---|
| How would you like to start? | **Custom setup** |
| Security disclaimer — "I understand this is personal-by-default…" | **Yes** |
| Help make OpenClaw better? | **No thanks** |
| What would you like to create? | **One agent** |
| What should we call your first agent? | **finanzas_personales** |
| How should I set things up? | **Ask first — check with me before looking around** |
| May I look around to find your AI access? | **No — I'll configure it manually** |
| Model/auth provider | **Skip for now** (el modelo se configura con `.env`, Paso 11) |

El instalador como servicio se omite: el gateway se levanta a mano.

**Verificación:**
```powershell
openclaw config file
```
Tiene que imprimir una ruta dentro de `TP_FINAL\openclaw\.openclaw\`. Confirmá además que el agente existe:
```powershell
openclaw config get agents
```
Debe mostrar `finanzas_personales` dentro de `entries`.

**Si falla:** si la ruta apunta a `C:\home\.openclaw\...`, el entorno del Paso 8 no estaba activo cuando corriste el onboarding. No lo repitas a ciegas: avisá al equipo con la salida de `openclaw config file`.

> Tené en cuenta el aviso de seguridad que aceptaste: OpenClaw es un agente personal pensado para un solo operador y no aísla usuarios por defecto. Para este proyecto se mitiga limitando sus tools solo a las 5 de finanzas (Paso 14) y decidiendo la identidad en el backend.

## 10. Elegir un modelo con cuota disponible

Algunos modelos no tienen cuota en el plan gratuito (devuelven `429` con `limit: 0`). Este script prueba tu clave contra los modelos disponibles y te dice cuáles responden:

```powershell
.\scripts\probe-models.ps1
```

Hace una llamada mínima por modelo (por defecto prueba los `flash`, `lite` y `gemma`). Salida esperada: una lista como

```text
gemini-xxx-flash        OK
gemini-yyy-pro          HTTP 429
```

Elegí uno que diga **OK** y escribilo en `LLM_MODEL` dentro de `openclaw\.env`.

**Si falla:**
- `No hay clave`: `LLM_API_KEY` está vacía en el `.env`.
- Todos dan `HTTP 429`: tu clave no tiene cuota en esos modelos. Probá `.\scripts\probe-models.ps1 -Pattern '.'` para probar todos, creá otra clave en Google AI Studio, o cambiá de proveedor (Paso 17).
- `HTTP 400` o `403`: la clave es inválida o no habilitada.

Después de editar el `.env`, **abrí una terminal nueva** y repetí el Paso 8 (las variables viejas no se pisan).

## 11. Aplicar la configuración del LLM

Estos comandos modifican `openclaw\.openclaw\openclaw.json`. Primero un respaldo:

```powershell
Copy-Item .openclaw\openclaw.json .openclaw\openclaw.json.bak
```

Probá el parche **sin aplicarlo**:
```powershell
openclaw config patch --file .\llm.patch.json5 --dry-run
```
**Verificación:** muestra los cambios previstos sin errores. Luego aplicalo:
```powershell
openclaw config patch --file .\llm.patch.json5
openclaw config validate
```
`validate` tiene que informar que la configuración es válida.

Qué hace `llm.patch.json5`: declara un proveedor genérico llamado `llm` cuyos valores salen del `.env` (`${LLM_BASE_URL}`, `${LLM_API_KEY}`, `${LLM_MODEL}`) y lo fija como modelo por defecto (`llm/<modelo>`). **No se vuelve a tocar:** cambiar de LLM después es solo editar el `.env` (Paso 17).

**Si falla:** pegá el mensaje exacto de error (ocultando claves). Si el esquema rechaza el modelo declarado, puede requerir campos adicionales para modelos personalizados; el mensaje indica cuáles.

## 12. Servidor MCP (las tools que ve el agente)

```powershell
cd tools-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
(`requirements.txt` fija `mcp>=1.2,<2`; la versión 2 renombró la API y rompe `server.py`.)

Verificá que importa. Con el entorno del Paso 8 activo, `BACKEND_URL` y las credenciales ya están cargadas:
```powershell
.\.venv\Scripts\python.exe -c "import server; print('ok')"
cd ..
```
Tiene que imprimir `ok`.

**Si falla:** `No module named 'server'` → estás en otra carpeta o falta `server.py` en `tools-mcp\`. `KeyError: 'BACKEND_URL'` → el entorno del Paso 8 no está activo en esta terminal. `No module named 'mcp'` → la instalación no terminó: `.\.venv\Scripts\python.exe -m pip list`.

## 13. Registrar workspace, tools y servidor MCP en OpenClaw

Abrí `openclaw.patch.json5` y reemplazá **las 4 apariciones** de esta ruta por la ruta real de tu proyecto (con barras `/` normales):

```text
C:/Users/Joel/Documents/facu/TP FINAL/TP_FINAL/openclaw
```
Por ejemplo `C:/Users/<vos>/<...>/TP_FINAL/openclaw`. Esas rutas son: el workspace (2 veces), el `command` (ejecutable de Python del venv del MCP) y el `cwd`.

Respaldá y probá:
```powershell
Copy-Item .openclaw\openclaw.json .openclaw\openclaw.json.bak
openclaw config patch --file .\openclaw.patch.json5 --dry-run
```
Si la vista previa es correcta:
```powershell
openclaw config patch --file .\openclaw.patch.json5
openclaw config validate
```

Qué configura:
- `agents…workspace`: el agente usa los archivos de `openclaw\workspace\` (reglas, tono, skill de finanzas).
- `tools`: perfil `minimal` + solo las tools del servidor MCP; **se deniegan** shell, archivos, navegador y canvas.
- `mcp.servers.finanzas`: cómo lanzar `server.py`, con `BACKEND_URL` y las credenciales leídas del entorno.

**Verificación** (los tres comandos):
```powershell
openclaw config get tools
openclaw config get mcp
openclaw config get agents
```
- `tools` muestra `"profile": "minimal"` y la lista `deny`.
- `mcp` muestra el servidor `finanzas`.
- `agents` muestra el workspace apuntando a tu carpeta `openclaw\workspace`.

## 14. Deshabilitar plugins que no se usan (recomendado)

El gateway carga plugins que no necesitás y que amplían la superficie de ataque (control de computadora, navegador, GitHub) o procesan conversaciones en segundo plano (`memory-core` crea un trabajo de "dreaming" que usa el LLM por su cuenta y escribe memoria a partir de las conversaciones, lo que choca con la regla de que los datos financieros viven solo en PostgreSQL). Uno por vez:

```powershell
openclaw plugins disable browser
openclaw plugins disable canvas
openclaw plugins disable cua-computer
openclaw plugins disable file-transfer
openclaw plugins disable github
openclaw plugins disable linux-node
openclaw plugins disable memory-core
```
Cada uno responde `Disabled plugin "<nombre>". Saved for the next Gateway start.` Los cambios se aplican en el próximo arranque del gateway. Si algo deja de funcionar, reactivalo con `openclaw plugins enable <nombre>`.

Chequeo de seguridad (revisá lo que marque):
```powershell
openclaw doctor
openclaw security audit --deep
```
Es esperable un aviso sobre el token del gateway en texto plano: es un entorno local; por eso `.openclaw\` está ignorado por git.

## 15. Levantar el gateway (terminal 3, la dejás abierta)

```powershell
cd "<ruta>\TP_FINAL\openclaw"
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

`start.ps1` activa el entorno del proyecto, comprueba que estén `LLM_BASE_URL`, `LLM_API_KEY` y `LLM_MODEL`, valida la configuración y arranca el gateway en primer plano.

**Verificación:** en la salida tienen que aparecer, entre otras:
```text
LLM: <tu modelo>  @  https://...
[gateway] agent model: llm/<tu modelo>
[gateway] http server listening (...)
[gateway] ready
```
Y la lista de plugins ya **no** incluye `browser`, `canvas` ni `memory-core`.

**Si falla:**
- `Faltan en .env`: completá `LLM_MODEL` (Paso 10).
- `La config no valida`: ejecutá `openclaw config validate` y corregí lo que indique.
- `#<Object> could not be cloned`: ver "Problemas conocidos" abajo.
- El archivo de log completo está en `%TEMP%\openclaw\`. Para ver el final en vivo:
  ```powershell
  Get-Content "$env:TEMP\openclaw\openclaw-$(Get-Date -Format yyyy-MM-dd).log" -Tail 50 -Wait
  ```

---

# PARTE C — Probar la llamada al backend, por capas

Probá en este orden. Si algo falla, **el primer nivel que falla te dice dónde está el problema**, sin adivinar si fue el LLM, OpenClaw, el MCP o el backend.

Terminal nueva para estas pruebas:
```powershell
cd "<ruta>\TP_FINAL\openclaw"
. .\scripts\use-project.ps1
$base = $env:BACKEND_URL
$login = Invoke-RestMethod -Method Post "$base/auth/login" -ContentType "application/json" -Body (@{email=$env:AGENT_USER_EMAIL; password=$env:AGENT_USER_PASSWORD} | ConvertTo-Json)
$h = @{ Authorization = "Bearer $($login.access_token)" }
```

## Capa 1 — El backend solo (sin LLM)

```powershell
Invoke-RestMethod "$base/tools/balance" -Headers $h | ConvertTo-Json -Depth 5
```
**Esperado:** `"status": "ok"` y un `balance` (250000 si usaste los saldos iniciales del Paso 5.5 y no hay movimientos).

Ahora un gasto **sin fecha**:
```powershell
$b = @{ amount = 1000; category = "Alimentacion"; account = "Efectivo" } | ConvertTo-Json
Invoke-RestMethod -Method Post "$base/tools/expense" -Headers $h -ContentType "application/json" -Body $b | ConvertTo-Json -Depth 5
```
**Esperado:** `"status": "needs_info"`, `"code": "MISSING_DATE"`, `"missing_fields": ["date"]`. Es el comportamiento correcto: **no se registró nada**, y el backend pide el dato en vez de asumirlo.

Ahora con fecha (esto **sí** crea un movimiento de prueba de $1.000):
```powershell
$b = @{ amount = 1000; date = (Get-Date -Format "yyyy-MM-dd"); category = "Alimentacion"; account = "Efectivo"; description = "prueba" } | ConvertTo-Json
Invoke-RestMethod -Method Post "$base/tools/expense" -Headers $h -ContentType "application/json" -Body $b | ConvertTo-Json -Depth 5
```
**Esperado:** `"status": "ok"` con `transaction_id`, `account`, `category`, `date`.

| Resultado | Causa probable |
|---|---|
| "No es posible conectar con el servidor remoto" | uvicorn no está corriendo. |
| `401` al iniciar sesión | El email/contraseña del `.env` no están registrados (Paso 5.5). |
| `404` en `/tools/...` | El backend corre un `main.py` viejo sin el router `tools`. |
| `needs_info` con `ACCOUNT_NOT_FOUND` / `CATEGORY_UNRESOLVED` | No existe esa cuenta o esa categoría. La respuesta lista las opciones válidas en `options`. |

## Capa 2 — El servidor MCP hacia el backend (sin LLM)

```powershell
.\tools-mcp\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'tools-mcp'); import server; print(server.get_balance())"
```
**Esperado:** el mismo sobre `status: ok`.

| Resultado | Causa probable |
|---|---|
| `UNAUTHENTICATED` | El usuario de `AGENT_USER_*` no existe o la contraseña no coincide. |
| `BACKEND_UNAVAILABLE` | uvicorn apagado o `BACKEND_URL` incorrecto. |

## Capa 3 — El LLM solo

Con el gateway corriendo (Paso 15), en otra terminal con el entorno activo:
```powershell
openclaw dashboard
```
Se abre el chat en el navegador. Escribí `hola`.

**Esperado:** una respuesta breve en español rioplatense como asistente de finanzas. Eso confirma que la clave, el modelo y la URL funcionan.

| Resultado | Causa probable |
|---|---|
| Error `401` / `403` en el log | Clave inválida o no habilitada. |
| Error `429` | Sin cuota para ese modelo: elegí otro en el Paso 10. |
| Responde como asistente genérico | El workspace no se está usando: revisá `openclaw config get agents`. |

## Capa 4 — La cadena completa (LLM → OpenClaw → MCP → backend → base)

En el chat del dashboard escribí:

> Pagué 20 lucas de luz

Mirá **la terminal de uvicorn** (la prueba real no está en la respuesta del chat, está ahí):

| Qué ves en uvicorn | Significado |
|---|---|
| `POST /auth/login ... 200` y luego `POST /tools/expense ... 200` | **Éxito:** el agente llamó a la tool. |
| Nada nuevo | El agente respondió sin usar tools o el MCP no cargó. Revisá `openclaw config get mcp` y `openclaw config get tools`, y el log del gateway. |
| `login ... 401` | Las credenciales `AGENT_USER_*` no coinciden con el usuario registrado. |
| `422` | Un parámetro llegó con formato inválido. |

**Esperado en el chat:** el agente **no registra todavía**. Falta la cuenta, así que pregunta algo como "¿Desde qué cuenta lo pagaste: Efectivo, Mercado Pago o Banco Nacion?". Que el log muestre `200` no significa que se haya guardado algo: una respuesta `needs_info` también es `200`.

Respondé:

> Mercado Pago

**Esperado:** el agente confirma el gasto de $20.000 en Servicios desde Mercado Pago. Verificá que quedó guardado en la base:

```powershell
Invoke-RestMethod "$base/tools/transactions?limit=5" -Headers $h | ConvertTo-Json -Depth 6
```
El movimiento tiene que aparecer con `amount` 20000, `account` "Mercado Pago" y `category` "Servicios".

## Capa 5 — Casos que deben fallar bien

Probá estos mensajes en el chat. El resultado correcto es el indicado:

| Mensaje | Qué tiene que pasar |
|---|---|
| `Me gasté unos pesos en comida` | No llama a ninguna tool; pregunta cuánto fue y desde qué cuenta. |
| `Anulá el último gasto` | Dice que todavía no está disponible; no registra nada. |
| `Ayer cobré 350 mil en el banco` | Registra un ingreso (puede preguntar la categoría); `date` = ayer. |
| `¿Cuánto gasté este mes?` | Llama a `get_expenses_by_category` y responde con los datos devueltos. |

Si el agente **registra algo sin preguntar un dato obligatorio** (por ejemplo, inventa la cuenta), anotá el mensaje exacto: es un error del agente a corregir en `workspace\AGENTS.md` o `skills\finanzas\SKILL.md`.

---

# Mantenimiento

## 16. Rutina diaria

1. `wsl -u root service postgresql start`
2. Terminal 1: `cd backend`, `.\venv\Scripts\Activate.ps1`, `uvicorn app.main:app --reload`
3. Terminal 3: `cd openclaw`, `powershell -ExecutionPolicy Bypass -File .\start.ps1`
4. Chat: `openclaw dashboard` (en una terminal con el entorno activo).

Para apagar: Ctrl+C en cada terminal y, si querés, `wsl -u root service postgresql stop`.

## 17. Cambiar de LLM (proveedor o modelo)

Editá solo estas tres líneas de `openclaw\.env`, abrí una terminal nueva y volvé a correr `start.ps1`:

```text
LLM_BASE_URL=...
LLM_API_KEY=...
LLM_MODEL=...
```
No hay que tocar la configuración de OpenClaw ni el backend. Después de cambiar de modelo, repetí las pruebas de la Capa 3 y 4: no todos los modelos siguen igual de bien las reglas del agente.

## 18. Problemas conocidos

| Síntoma | Qué sabemos |
|---|---|
| `#<Object> could not be cloned` al refrescar el catálogo de modelos (`openclaw models list --refresh`) | Error de OpenClaw 2026.11.4 en Windows, **aún sin resolver**. Es independiente de la clave y del backend. Esta guía declara el modelo directamente en la configuración (`llm.patch.json5`) para no depender del catálogo, pero **no está verificado** que eso lo evite en todos los casos. Si el gateway o el chat fallan con ese mensaje, guardá el log completo y consultalo antes de probar soluciones. Una alternativa es correr OpenClaw dentro de WSL2 (instalación Linux oficial); no está probada en este proyecto. |
| `429` con `limit: 0` | El modelo elegido no tiene cuota gratuita. Usá el Paso 10. |
| `openclaw doctor` avisa del token en texto plano | Esperado en desarrollo local. Mantené `.openclaw\` fuera de git. |
| Aviso `DEP_PLUGIN_SDK` al arrancar | Aviso de deprecación; no afecta. |
| El agente pregunta por `date` | Si el mensaje no menciona fecha, el skill indica enviar la de hoy; si el modelo no conoce la fecha actual, la pregunta. Revisá el modelo elegido. |
| `Remove-Item`/`Copy-Item` pegados en una sola línea | Pegá un comando por vez. |

## 19. Seguridad y privacidad (qué no hacer)

- Nunca subas `.env`, `.openclaw\`, `.venv\` ni respaldos `*.bak`.
- `.openclaw\` guarda **conversaciones de usuarios** (mensajes con montos y hábitos de gasto): tratalo como dato sensible.
- Con un plan gratuito de un proveedor externo, usá **solo datos de prueba**.
- El usuario `AGENT_USER_*` es una cuenta de desarrollo: este modo (una sola identidad para todo el agente) **no sirve para multiusuario real**. Cómo llega el token de cada usuario a la sesión del agente es una decisión pendiente del proyecto.

## 20. Checklist final

- [ ] `Test-NetConnection localhost -Port 5432` → `True`
- [ ] `http://localhost:8000/docs` muestra los 5 endpoints `/tools`
- [ ] `openclaw --version` → 2026.11.4
- [ ] `openclaw config file` → ruta dentro de `TP_FINAL\openclaw\.openclaw\`
- [ ] `openclaw config validate` → válida
- [ ] `openclaw config get tools` → perfil `minimal`
- [ ] `openclaw config get mcp` → servidor `finanzas`
- [ ] Gateway: `agent model: llm/<modelo>` y `ready`
- [ ] Capa 1 a 4 de la prueba superadas
- [ ] "Pagué 20 lucas de luz" → pregunta la cuenta → al responderla queda registrado
