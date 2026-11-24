# Plataforma Conversacional de Finanzas Personales

Aplicación web para registrar, administrar y consultar gastos e ingresos mediante lenguaje natural, utilizando inteligencia artificial para interpretar las solicitudes y un backend propio para ejecutar las operaciones financieras.

El sistema está desarrollado con **React, FastAPI, PostgreSQL y Gemini**.

Su principio central es:

> **El agente interpreta. El backend decide.**

El modelo de IA interpreta las solicitudes del usuario, pero las operaciones financieras son validadas y ejecutadas exclusivamente por el backend.

---

## Problema

El control cotidiano de las finanzas personales requiere registrar gastos e ingresos con frecuencia. Sin embargo, muchas aplicaciones obligan a completar manualmente formularios con monto, fecha, categoría, cuenta y descripción para cada movimiento.

Esta fricción puede provocar registros incompletos, falta de continuidad o abandono del seguimiento financiero.

La propuesta busca simplificar ese proceso permitiendo utilizar expresiones cotidianas como:

> "Gasté 18.500 en supermercado desde Mercado Pago."

En lugar de completar todos los campos manualmente, el usuario puede comunicar la operación mediante una conversación.

---

## Usuario objetivo y validación

El producto está orientado a personas que desean controlar sus finanzas personales, pero buscan una alternativa más ágil que la carga manual tradicional.

Para validar el problema se realizó una encuesta a **47 participantes reales**.

Entre los resultados obtenidos:

- **74,5 %** lleva algún tipo de registro de sus finanzas.
- **55,3 %** realiza ese registro solo ocasionalmente.
- **53,2 %** indicó que suele olvidarse de registrar movimientos.
- **42,6 %** considera tedioso el proceso de registrarlos.
- **91,5 %** utiliza más de una cuenta, banco o billetera.
- **74,5 %** prefiere que el sistema consulte antes de registrar una operación cuando falta información sobre la cuenta.
- **76,6 %** indicó que seguramente o probablemente utilizaría una herramienta de este tipo.

Estos resultados respaldaron la decisión de desarrollar un asistente conversacional que reduzca la carga manual, permita administrar múltiples cuentas y solicite aclaraciones cuando falte información.

Los resultados completos se encuentran en [docs/validacion-usuarios.md](docs/validacion-usuarios.md).

---

## Solución implementada

La aplicación permite administrar información financiera mediante una interfaz web tradicional y un asistente de inteligencia artificial.

Por ejemplo, ante el mensaje:

> "Gasté 12.500 en una pizza con Juan."

Gemini puede interpretar que el usuario desea registrar un gasto de $12.500 relacionado con alimentación.

Si el usuario no indicó desde qué cuenta realizó el pago, el sistema debe solicitar esa información antes de registrar el movimiento.

Por ejemplo:

> "Entendí que gastaste $12.500 en alimentación. ¿Desde qué cuenta lo pagaste?"

Cuando dispone de los datos necesarios, FastAPI valida la operación y la registra en PostgreSQL.

La interpretación de Gemini **no implica autorización automática para ejecutar una operación**.

---

## Funcionalidades del P0

### Autenticación y usuarios

- Registro de usuarios.
- Inicio de sesión.
- Contraseñas almacenadas mediante hash.
- Autenticación con JWT.
- Validación de contraseñas.
- Separación de datos entre usuarios.

### Gestión de cuentas

- Creación y consulta de cuentas.
- Tipos `CASH`, `BANK` y `WALLET`.
- Definición de saldo inicial.
- Consulta del saldo por cuenta.
- Desactivación lógica de cuentas.
- Validación de nombres y saldos iniciales.
- Prevención de nombres duplicados entre cuentas activas del mismo usuario.

### Gestión de movimientos

- Registro de ingresos.
- Registro de gastos.
- Asociación a cuentas y categorías.
- Consulta del historial.
- Filtros por fecha, tipo, cuenta y categoría.
- Anulación lógica de movimientos.
- Validación de montos, fechas y permisos.

### Consultas financieras

- Saldo general.
- Saldo de una cuenta.
- Consulta de movimientos.
- Consulta de gastos agrupados por categoría.

### Asistente conversacional

- Interpretación de lenguaje natural mediante Gemini.
- Identificación de operaciones financieras.
- Selección de herramientas mediante *function calling*.
- Solicitud de información faltante.
- Resolución conversacional de aclaraciones.
- Validación de parámetros antes de ejecutar operaciones.
- Respuestas en lenguaje natural.

### Auditoría conversacional

- Registro de mensajes procesados por `/chat`.
- Registro de herramientas solicitadas y decisiones del backend.
- Asociación con el movimiento generado, cuando corresponde.
- Registro de respuestas y errores del proveedor de IA.

La auditoría corresponde al canal conversacional y no cubre integralmente todas las operaciones REST.

---

## Arquitectura general

La aplicación utiliza una arquitectura modular que separa la interfaz, el procesamiento conversacional, las reglas de negocio y la persistencia.

```text
Usuario
   |
   v
React (interfaz web)
   |
   v
FastAPI (POST /chat)
   |
   +------> Gemini (interpretación)
   |             |
   |<------------+
   |
   v
Herramienta solicitada
   |
   v
Validaciones y reglas de negocio
   |
   v
PostgreSQL
   |
   v
Respuesta al usuario
```

### Responsabilidades

**React:** presenta la información y permite administrar cuentas, movimientos y conversaciones.

**Gemini:** interpreta las solicitudes y propone herramientas con parámetros estructurados.

**FastAPI:** autentica usuarios, valida parámetros, aplica reglas financieras y ejecuta las operaciones.

**PostgreSQL:** almacena los datos financieros y los registros de auditoría.

El frontend no se comunica directamente con Gemini ni con PostgreSQL.

La orquestación conversacional se realiza desde FastAPI, sin necesidad de un gateway adicional.

La arquitectura se explica con mayor detalle en [docs/arquitectura.md](docs/arquitectura.md).

### Integración alternativa con OpenClaw

El repositorio conserva la carpeta `openclaw/`, que contiene una integración alternativa mediante OpenClaw y MCP.

Sin embargo, **OpenClaw no forma parte del flujo principal del P0**.

Tanto el desarrollo local como el despliegue web utilizan la integración directa entre FastAPI y Gemini.

El cliente del LLM emplea una interfaz compatible con Chat Completions de OpenAI, lo que permite configurar proveedores compatibles mediante variables de entorno.

---

## Herramientas conversacionales

El asistente dispone de cinco herramientas:

| Herramienta | Función |
|---|---|
| `create_expense` | Registrar un gasto |
| `create_income` | Registrar un ingreso |
| `get_balance` | Consultar saldos |
| `get_transactions` | Consultar movimientos |
| `get_expenses_by_category` | Consultar gastos agrupados por categoría |

Gemini propone la herramienta y sus parámetros.

FastAPI comprueba que la solicitud cumpla las reglas de negocio antes de ejecutarla.

El backend admite como máximo **una operación de escritura exitosa por mensaje**.

El contrato de cada herramienta se encuentra en [docs/tools.md](docs/tools.md).

---

## Validaciones financieras

El backend aplica reglas determinísticas para evitar operaciones inválidas.

Entre las validaciones implementadas:

- El usuario debe estar autenticado.
- Las cuentas deben pertenecer al usuario y estar activas.
- Los importes deben ser mayores que cero.
- Se admiten como máximo dos decimales.
- El importe máximo permitido es `9999999999999.99`.
- No se permiten fechas futuras.
- Las categorías deben existir y corresponder al tipo de movimiento.
- El sistema trabaja exclusivamente con pesos argentinos (`ARS`).
- Los movimientos anulados no deben afectar los saldos.
- Los parámetros inválidos recibidos desde la IA deben rechazarse.

Las validaciones compartidas de importes y fechas se encuentran en:

`backend/app/services/transaction_validation.py`

### Información faltante y ambigüedades

Si el usuario escribe:

> "Gasté 20.000 ayer."

El sistema puede identificar el importe y la fecha, pero necesita conocer la cuenta y la categoría.

En ese caso, no debe registrar el gasto hasta disponer de la información necesaria.

Las herramientas devuelven resultados estructurados:

- `ok`: operación completada.
- `needs_info`: falta información o existe una ambigüedad.
- `rejected`: la solicitud no cumple las reglas.

El backend incorpora controles para detectar determinadas solicitudes ambiguas, tanto en gastos como en ingresos.

En particular, cuando un usuario informa un ingreso sin especificar su origen, el sistema solicita una aclaración antes de registrarlo, evitando que Gemini asigne automáticamente una categoría sin información suficiente.

Por ejemplo, ante «Me entraron 50.000 en Mercado Pago», el asistente debe preguntar si corresponde a Sueldo, Honorarios, Inversiones u Otros.

La protección contempla patrones conocidos y no garantiza detectar todas las interpretaciones incorrectas del modelo.

---

## Alcance financiero

Las cuentas de la plataforma son **representaciones informativas creadas por el usuario**.

La aplicación no realiza transferencias de dinero ni operaciones sobre bancos, billeteras virtuales, tarjetas o procesadores de pago.

### Tipos de cuenta

- Efectivo (`CASH`).
- Cuenta bancaria (`BANK`).
- Billetera virtual (`WALLET`).

### Moneda

El P0 trabaja exclusivamente en pesos argentinos (`ARS`).

### Cálculo de saldos

El saldo se calcula a partir del saldo inicial y los movimientos activos:

```text
Saldo actual =
    saldo inicial
  + ingresos activos
  - gastos activos
```

Los movimientos anulados (`VOIDED`) no afectan el saldo.

El saldo general considera únicamente las cuentas activas.

Los importes representan la información registrada dentro de la aplicación, no los saldos reales de entidades financieras.

---

## Modelo de datos

El sistema utiliza cinco entidades principales:

- `User`: usuarios registrados.
- `Account`: cuentas pertenecientes a cada usuario.
- `Category`: categorías predefinidas.
- `Transaction`: ingresos y gastos registrados.
- `AuditLog`: auditoría del procesamiento conversacional.

La relación financiera principal es:

```text
User
  |
  +--- Account
          |
          +--- Transaction --- Category

User
  |
  +--- AuditLog
```

La propiedad de cada movimiento se determina mediante:

`Transaction → Account → User`

La tabla `audit_logs` conserva el identificador de la transacción asociada cuando corresponde, aunque actualmente ese campo no posee una restricción de clave foránea.

El esquema completo está documentado en [docs/modelo-datos.md](docs/modelo-datos.md).

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Frontend | React + Vite |
| Procesamiento conversacional | Gemini |
| Orquestación | FastAPI + function calling |
| Backend | Python + FastAPI |
| Validación | Pydantic |
| ORM | SQLAlchemy |
| Base de datos | PostgreSQL |
| Migraciones | Alembic |
| Autenticación | JWT |
| Testing | pytest |
| Evaluación conversacional | Python + Gemini |
| Control de versiones | Git + GitHub |
| Despliegue | Render |
| Integración alternativa | OpenClaw + MCP |

El despliegue se configura mediante `render.yaml`.

No se requiere Docker para ejecutar el P0 ni para el despliegue utilizado.

---

## Estructura del repositorio

```text
TP_FINAL/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── evaluacion/
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
│
├── frontend/
│   └── ...
│
├── openclaw/
│   └── ...
│
├── database/
├── docs/
│   ├── arquitectura.md
│   ├── modelo-datos.md
│   ├── modulos.md
│   ├── tools.md
│   ├── validacion-usuarios.md
│   └── evaluacion-nl.md
│
├── render.yaml
└── README.md
```

### Carpetas principales

**`backend/`** contiene la API, las reglas de negocio, la integración con Gemini, las migraciones y las pruebas automatizadas.

**`frontend/`** contiene la aplicación React utilizada para autenticación, gestión financiera y conversación con el asistente.

**`openclaw/`** conserva los archivos de la integración alternativa, que no se ejecuta en el flujo principal del P0.

**`database/`** contiene documentación complementaria de la base de datos.

**`docs/`** contiene la documentación funcional y técnica.

---

## Instalación y ejecución local

### Requisitos

- Python 3.12 o superior.
- Node.js 20 o superior.
- PostgreSQL.
- Una API key válida de Gemini para utilizar el asistente conversacional.

### Backend

Desde la raíz del repositorio:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Crear el archivo de configuración:

```powershell
Copy-Item .env.example .env
```

Completar en `backend/.env` las variables necesarias, entre ellas:

```dotenv
DATABASE_URL=postgresql+psycopg://usuario:password@localhost:5432/finanzas
JWT_SECRET_KEY=tu_clave_secreta
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_API_KEY=tu_api_key_de_gemini
LLM_MODEL=nombre_del_modelo_habilitado
```

Los valores son ilustrativos y deben reemplazarse por la configuración real.

La aplicación puede utilizar distintos modelos de Gemini compatibles con la API. El modelo se selecciona mediante `LLM_MODEL`, sin modificar el código financiero.

Aplicar las migraciones:

```powershell
alembic upgrade head
```

Cargar los datos iniciales:

```powershell
python -m app.seed
```

Iniciar FastAPI:

```powershell
uvicorn app.main:app --reload
```

Backend local:

`http://127.0.0.1:8000`

Documentación interactiva:

`http://127.0.0.1:8000/docs`

### Frontend

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Aplicación local:

`http://localhost:5173`

Durante el desarrollo, Vite utiliza un proxy para reenviar las solicitudes `/api` al backend.

### OpenClaw

No es necesario instalar ni ejecutar OpenClaw para utilizar la aplicación.

Los archivos de su integración alternativa permanecen en `openclaw/`.

---

## Seguridad y privacidad

El sistema implementa los siguientes mecanismos:

- Contraseñas almacenadas mediante hash.
- Autenticación mediante JWT.
- Identificación del usuario exclusivamente desde el backend.
- Validación de propiedad de cuentas y movimientos.
- Separación de información entre usuarios.
- Validaciones financieras independientes de Gemini.
- Gestión de credenciales mediante variables de entorno.
- Acceso a PostgreSQL exclusivamente desde FastAPI.
- Ausencia de acceso directo del LLM a la base de datos.

### Tratamiento de la información

| Información | Tratamiento |
|---|---|
| Usuarios | Se almacena correo electrónico y hash de contraseña |
| Cuentas y movimientos | Se almacenan en PostgreSQL |
| Mensajes del chat | Se registran en `audit_logs` |
| Mensajes enviados al LLM | Se transmite el mensaje y el contexto conversacional necesario |
| Resultados de herramientas | Pueden incluir cuentas, categorías y montos |
| Credenciales y JWT | No forman parte de los parámetros enviados deliberadamente al LLM |
| API keys | Se configuran mediante variables de entorno |

### Errores del proveedor de IA

Las solicitudes al modelo pueden fallar por problemas de conectividad, disponibilidad, saturación o límites de uso.

El backend contempla el manejo controlado de estos errores y puede utilizar un modelo de respaldo cuando está configurado.

Una falla anterior a la ejecución de una operación financiera no debe producir modificaciones.

Si una operación ya fue confirmada por el backend antes de una falla posterior del proveedor, el movimiento registrado se conserva. Por ese motivo, no debe asumirse automáticamente que una solicitud fallida no produjo ninguna escritura.

---

## Estrategia de pruebas

Se utilizan dos mecanismos complementarios.

### Pruebas automatizadas con pytest

Las pruebas del backend comprueban:

- Registro y autenticación.
- Separación de usuarios.
- Creación y validación de cuentas.
- Validación de contraseñas.
- Registro de ingresos y gastos.
- Validación de montos y fechas.
- Manejo de parámetros inválidos enviados por el LLM.
- Anulación lógica de movimientos.
- Cálculo de saldos.
- Consultas y reportes.
- Comportamiento del canal conversacional.
- Límites de escritura por mensaje.
- Manejo de errores del proveedor.

La última ejecución realizada después de las correcciones del backend finalizó con:

**80 tests aprobados.**

Para ejecutar las pruebas:

```powershell
cd backend
pytest
```

Las pruebas utilizan un entorno controlado, con SQLite y respuestas simuladas del proveedor de IA, sin requerir una API key real de Gemini.

### Evaluación de lenguaje natural

La carpeta `backend/evaluacion/` contiene **60 consultas de prueba**, clasificadas por comportamiento esperado:

- `registra`.
- `pregunta`.
- `rechaza`.
- `consulta`.
- `sin_accion`.

El script permite enviar estas consultas a `/chat` utilizando el proveedor de IA configurado.

Desde `backend/`:

```powershell
python evaluacion/evaluar.py --url http://127.0.0.1:8000
```

Los resultados se documentan en [docs/evaluacion-nl.md](docs/evaluacion-nl.md).

En la segunda evaluación documentada del despliegue se obtuvieron **58 casos correctos sobre 60 (aproximadamente 97 %)** y se identificó una operación incorrecta ejecutada sin aclaración.

Posteriormente se incorporaron mejoras de validación y controles de ambigüedad.

**Ese resultado corresponde a la evaluación documentada anteriormente y no representa una nueva ejecución posterior a todas las correcciones recientes.**

Las pruebas automatizadas y la evaluación conversacional cumplen objetivos diferentes: las primeras verifican reglas y comportamientos controlados; la segunda analiza la interpretación real del lenguaje natural.

---

## Despliegue

El proyecto cuenta con una configuración de despliegue en Render mediante [render.yaml](render.yaml).

Los enlaces documentados son:

| Componente | Dirección |
|---|---|
| Aplicación web | https://finanzas-tpfinal-web.onrender.com |
| API y Swagger | https://finanzas-tpfinal-api.onrender.com/docs |
| Base de datos | PostgreSQL administrado por Render |

El despliegue utiliza la API directa de Gemini y no necesita ejecutar OpenClaw.

### Consideraciones del plan gratuito

El backend puede suspenderse después de un período de inactividad, por lo que la primera solicitud puede presentar una demora adicional.

La base PostgreSQL utilizada en el despliegue original fue creada el **20/11/2026** en el plan gratuito de Render, con un plazo de aproximadamente 30 días.

Por lo tanto, será necesario revisar su vigencia alrededor del **20/12/2026** y, si corresponde, migrar o recrear la base en otro servicio.

El backend está configurado para aplicar las migraciones y cargar las categorías al iniciar.

La recreación de una base de datos no conserva automáticamente los movimientos previamente registrados si no se realiza una migración o respaldo de esos datos.

---

## Prioridades y funcionalidades futuras

El desarrollo se organiza en tres niveles.

### P0 — Núcleo funcional

Incluye autenticación, cuentas, movimientos, categorías, consultas, asistente conversacional, validaciones financieras, auditoría del chat y despliegue web.

### P1 — Ampliaciones

- Transferencias internas.
- Categorías personalizadas.
- Movimientos recurrentes.
- Presupuestos.
- Múltiples monedas.
- Tarjetas de crédito.
- Reportes adicionales.

### P2 — Funcionalidades futuras

- Integraciones con entidades financieras.
- Análisis financiero avanzado.
- Canales conversacionales adicionales.
- Automatizaciones.

También se identificaron posibles mejoras técnicas:

- Idempotencia para evitar movimientos duplicados por reintentos.
- Paginación de listados extensos.
- Limitación de intentos de inicio de sesión.
- Auditoría integral de operaciones REST.
- Restricciones adicionales de integridad referencial.
- Mejoras de interfaz, confirmaciones y notificaciones.

Estas mejoras no forman parte del alcance funcional obligatorio del P0.

El listado completo de módulos se encuentra en [docs/modulos.md](docs/modulos.md).

---

## Documentación

| Documento | Contenido |
|---|---|
| [Arquitectura](docs/arquitectura.md) | Componentes, tecnologías y flujo conversacional |
| [Modelo de datos](docs/modelo-datos.md) | Entidades, relaciones y decisiones de diseño |
| [Módulos](docs/modulos.md) | Funcionalidades y prioridades |
| [Contratos de tools](docs/tools.md) | Herramientas, parámetros y validaciones |
| [Validación con usuarios](docs/validacion-usuarios.md) | Encuesta y análisis de resultados |
| [Evaluación conversacional](docs/evaluacion-nl.md) | Pruebas de lenguaje natural y resultados |

El informe académico final se entregará como documento PDF independiente.

---

## Estado actual del proyecto

El núcleo funcional P0 se encuentra implementado.

Incluye:

- Autenticación y separación de datos por usuario.
- Administración de cuentas.
- Ingresos y gastos.
- Anulación lógica de movimientos.
- Consultas financieras.
- Asistente conversacional con Gemini.
- Validaciones compartidas entre REST y herramientas.
- Manejo de aclaraciones y determinados casos ambiguos.
- Auditoría conversacional.
- Pruebas automatizadas.
- Evaluación de lenguaje natural.
- Configuración de despliegue en Render.

La última ejecución de pruebas del backend registró *80 tests aprobados**.

El proyecto continúa en una etapa de revisión documental y refinamiento de la experiencia de usuario.

---

## Equipo

**Integrantes:**
- Joel Andrés Gonzalo Aguilar
- Matías José Alochis
- Lucas Esteban Zupan

**Tutor:** Oscar Londero

### Experiencia previa del equipo

Nivel de experiencia declarado al definir el stack tecnológico:

| Tecnología | Aguilar | Alochis | Zupan |
|---|---|---|---|
| Python | Avanzado | Intermedio | Inicial |
| FastAPI | Intermedio | Inicial | Inicial |
| PostgreSQL | Intermedio | Inicial | Intermedio |
| React | Inicial | Inicial | Intermedio |
| Docker | Inicial | Inicial | Inicial |
| OpenClaw | Inicial | Inicial | Inicial |
| Integración con LLM | Intermedio | Intermedio | Inicial |

Escala utilizada:

- **Inicial:** conocimientos introductorios o poca experiencia práctica.
- **Intermedio:** capacidad para desarrollar funcionalidades con documentación y apoyo puntual.
- **Avanzado:** capacidad para trabajar autónomamente y resolver problemas habituales.

Esta evaluación contribuyó a definir un alcance técnico realizable. Durante el desarrollo se decidió utilizar Gemini directamente desde FastAPI, evitando mantener OpenClaw como dependencia del flujo principal.

---

## Derechos de autor

Copyright © 2026 Joel Andrés Gonzalo Aguilar, Matías José Alochis y Lucas Esteban Zupan.

**Todos los derechos reservados.**

Este proyecto fue desarrollado con fines académicos. No se concede autorización general para copiar, modificar, redistribuir o comercializar su código sin el consentimiento de sus autores, salvo los usos permitidos por la legislación aplicable y los términos de GitHub.