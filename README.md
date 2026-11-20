# Plataforma Conversacional de Finanzas Personales

Asistente financiero personal que permite registrar y consultar gastos e ingresos mediante lenguaje natural a través de una interfaz conversacional.

El sistema utiliza **OpenClaw como capa de orquestación del agente de IA** y un backend propio como única autoridad sobre las reglas de negocio, la autorización y la persistencia de la información.

> **El agente interpreta. El backend decide.**

---

## Problema

El control cotidiano de las finanzas personales requiere registrar de manera frecuente gastos e ingresos. Sin embargo, muchas herramientas disponibles requieren completar manualmente formularios indicando monto, fecha, categoría, cuenta y descripción para cada movimiento.

Esta fricción puede provocar que las personas registren sus movimientos de manera incompleta, irregular o directamente abandonen el seguimiento de sus finanzas personales.

La propuesta busca reducir esa fricción permitiendo registrar y consultar movimientos mediante expresiones cotidianas como:

> "Gasté 18.500 en supermercado desde Mercado Pago."

en lugar de completar manualmente cada uno de los campos de un formulario tradicional.

---

## Usuario objetivo

El producto está orientado a personas que desean llevar un control de sus finanzas personales mediante el registro de ingresos y gastos, pero buscan una alternativa más ágil que la carga manual tradicional.

La validación realizada con potenciales usuarios mostró, entre otros resultados:

- **74,5 %** lleva algún tipo de registro de sus finanzas.
- **55,3 %** realiza ese registro solo ocasionalmente.
- **53,2 %** indicó que suele olvidarse de registrar movimientos.
- **42,6 %** considera tedioso el proceso de registrarlos.
- **91,5 %** utiliza más de una cuenta, banco o billetera.
- **74,5 %** prefiere que el sistema consulte antes de registrar una operación cuando falta información sobre la cuenta.
- **76,6 %** indicó que seguramente o probablemente utilizaría una herramienta de este tipo.

Los resultados completos se encuentran documentados en:

[`docs/validacion-usuarios.md`](docs/validacion-usuarios.md)

---

## Solución propuesta

La aplicación permitirá al usuario registrar y consultar información financiera mediante lenguaje natural.

Por ejemplo:

> "Gasté 12.500 en una pizza con Juan."

La capa conversacional interpretará el mensaje y determinará la intención del usuario y los datos disponibles.

Una interpretación posible sería:

```json
{
  "operacion": "gasto",
  "monto": 12500,
  "moneda": "ARS",
  "categoria_sugerida": "alimentacion",
  "fecha": null,
  "cuenta": null,
  "descripcion": "pizza con Juan"
}
```

Esta interpretación **no implica que la operación pueda ejecutarse automáticamente**.

El backend recibe la solicitud estructurada y aplica las validaciones de autenticación, autorización, integridad y reglas de negocio correspondientes.

Si falta información obligatoria, el sistema no debe inventarla.

Por ejemplo:

> "Entendí que gastaste $12.500 en alimentación. ¿Desde qué cuenta lo pagaste?"

Una vez obtenida y validada toda la información necesaria, el backend podrá ejecutar la operación y persistirla en PostgreSQL.

---

## Arquitectura general

El sistema utiliza una arquitectura modular con separación entre la capa conversacional, la lógica de negocio y la persistencia.

```text
Usuario
   ↓
Interfaz Web
   ↓
OpenClaw
   ↓
Agente / LLM
   ↓
Tool / solicitud estructurada
   ↓
Backend FastAPI
   ↓
Validación + autorización + reglas de negocio
   ↓
PostgreSQL
   ↓
Respuesta al usuario
```

### Responsabilidades principales

**Interfaz Web**

Proporciona el canal de interacción con el usuario.

**OpenClaw**

Gestiona la orquestación del agente conversacional, el contexto de la conversación y la invocación de las tools disponibles.

**Agente / LLM**

Interpreta el lenguaje natural, identifica la intención y extrae los parámetros necesarios para solicitar una operación.

**FastAPI**

Constituye el backend de la aplicación y es responsable de:

- autenticación;
- autorización;
- validaciones;
- reglas de negocio;
- acceso a los datos;
- ejecución de operaciones financieras;
- aislamiento de información entre usuarios.

**PostgreSQL**

Constituye la fuente persistente de verdad del sistema.

OpenClaw y el LLM **no acceden directamente a PostgreSQL ni contienen las reglas financieras del sistema**.

La arquitectura completa se encuentra documentada en:

[`docs/arquitectura.md`](docs/arquitectura.md)

---

## Tools y comunicación con el backend

La comunicación entre la capa conversacional y el backend se realizará mediante **tools con entradas estructuradas y previamente definidas**.

Para el alcance P0 se contemplan inicialmente:

```text
create_expense(...)
create_income(...)
get_balance(...)
get_transactions(...)
get_expenses_by_category(...)
```

El agente podrá seleccionar una tool y proporcionar los parámetros interpretados, pero la decisión de ejecutar una operación corresponderá siempre al backend.

Por ejemplo:

```text
Usuario
"Gasté $18.500 en supermercado con Mercado Pago"
        ↓
OpenClaw + LLM
interpreta la intención
        ↓
create_expense(...)
        ↓
Backend
valida usuario, cuenta, monto, categoría y reglas
        ↓
PostgreSQL
persiste el movimiento
        ↓
Respuesta al usuario
```

Los contratos y responsabilidades de cada tool están documentados en:

[`docs/tools.md`](docs/tools.md)

---

## Manejo de información faltante y ambigüedades

El modelo de lenguaje puede interpretar la intención del usuario, pero no debe inventar información necesaria para ejecutar una operación.

Por ejemplo:

> "Gasté 20.000 ayer."

Si la cuenta es un dato obligatorio y no puede determinarse de forma segura, el sistema deberá solicitarla antes de registrar el movimiento.

La decisión final dependerá de reglas determinísticas implementadas en el backend.

Entre las validaciones previstas se encuentran:

- monto obligatorio ausente → solicitar información;
- monto inválido → rechazar;
- cuenta obligatoria ausente → solicitar información;
- cuenta inexistente → solicitar corrección;
- cuenta perteneciente a otro usuario → rechazar;
- categoría no identificada de forma segura → solicitar aclaración;
- información contradictoria → no ejecutar;
- usuario no autenticado → rechazar;
- usuario no autorizado → rechazar.

Las operaciones de consulta estarán sujetas a los mismos mecanismos de autenticación y autorización que las operaciones de escritura.

---

## Alcance del MVP

El desarrollo se organiza por prioridades **P0, P1 y P2**.

### P0 — Núcleo obligatorio

Incluye las funcionalidades necesarias para demostrar el funcionamiento completo del producto:

- registro e inicio de sesión;
- gestión básica de cuentas;
- categorías predefinidas;
- registro de gastos;
- registro de ingresos;
- consulta de saldo;
- consulta de movimientos;
- consulta de gastos por categoría;
- interpretación de lenguaje natural;
- detección de información faltante;
- resolución conversacional de ambigüedades;
- validaciones determinísticas en el backend;
- aislamiento de información entre usuarios;
- interfaz web;
- integración con OpenClaw y un LLM.

### P1 — Ampliaciones

Una vez completado y estabilizado P0 podrán evaluarse:

- transferencias internas;
- categorías personalizadas;
- movimientos recurrentes;
- presupuestos;
- soporte para múltiples monedas;
- tarjetas de crédito;
- consultas y reportes adicionales.

### P2 — Funcionalidades opcionales

Como posibles ampliaciones futuras podrán evaluarse:

- integraciones con instituciones o servicios financieros;
- análisis financiero avanzado;
- canales conversacionales adicionales;
- automatizaciones adicionales.

La definición completa de los módulos y sus prioridades se encuentra en:

[`docs/modulos.md`](docs/modulos.md)

---

## Alcance financiero

Las cuentas utilizadas dentro de la plataforma son **representaciones informativas creadas por el usuario**.

La aplicación no realizará operaciones reales sobre:

- cuentas bancarias;
- billeteras virtuales;
- tarjetas;
- procesadores de pago;
- servicios financieros externos.

### Cuentas P0

El MVP trabajará inicialmente con:

- efectivo (`CASH`);
- cuentas bancarias (`BANK`);
- billeteras virtuales (`WALLET`).

### Moneda

P0 trabajará exclusivamente con **pesos argentinos (ARS)**.

El soporte para múltiples monedas queda fuera del alcance inicial.

### Saldos

Los saldos serán calculados a partir del saldo inicial registrado por el usuario y sus movimientos activos:

```text
Saldo =
saldo inicial
+ ingresos activos
- gastos activos
```

El saldo mostrado por la aplicación representa exclusivamente la información registrada dentro del sistema y no el saldo real existente en una institución financiera.

---

## Modelo de datos

El modelo inicial está compuesto por cuatro entidades principales:

```text
User
  │
  └──< Account
          │
          └──< Transaction >── Category
```

Las relaciones principales son:

- un usuario puede poseer múltiples cuentas;
- cada cuenta pertenece a un único usuario;
- una cuenta puede registrar múltiples movimientos;
- cada movimiento pertenece a una cuenta;
- una categoría puede clasificar múltiples movimientos;
- cada movimiento posee una categoría.

La pertenencia de una transacción a un usuario se determina mediante su cuenta:

```text
Transaction → Account → User
```

El diseño completo, tipos de datos, claves primarias, claves foráneas, índices y diagrama entidad-relación se encuentran en:

[`docs/modelo-datos.md`](docs/modelo-datos.md)

---

## Stack tecnológico

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Frontend | React | Interfaz web |
| Orquestación | OpenClaw | Gestión del agente y ejecución de tools |
| Inteligencia artificial | API de LLM | Interpretación de lenguaje natural |
| Backend | Python + FastAPI | API y reglas de negocio |
| Validación | Pydantic | Validación de entradas y salidas |
| ORM | SQLAlchemy | Acceso a datos |
| Base de datos | PostgreSQL | Persistencia |
| Migraciones | Alembic | Versionado del esquema |
| Autenticación | JWT | Identificación de usuarios |
| Testing | pytest | Pruebas unitarias y de integración |
| Proveedor de IA | Gemini Flash (`gemini-flash-latest`) | Modelo usado en el despliegue (API compatible con OpenAI) |
| Despliegue | Render | PostgreSQL, backend y frontend online (`render.yaml`) |
| Control de versiones | Git + GitHub | Versionado y colaboración |

El backend se comunica con la IA mediante el formato de Chat Completions de OpenAI. Así, el mismo código funciona con el gateway de OpenClaw en desarrollo y con Gemini en el despliegue, y se puede cambiar de proveedor sin modificar la lógica financiera. Docker se descartó porque el despliegue en Render no lo requiere.

---

## Seguridad y privacidad

Debido a que el sistema manejará información financiera personal, se establecen los siguientes criterios:

- todas las operaciones requieren autenticación;
- las contraseñas se almacenan mediante hashing;
- las credenciales y API keys se gestionan mediante variables de entorno;
- el backend determina la identidad del usuario autenticado;
- el LLM nunca determina qué usuario es propietario de una operación;
- cada recurso es validado contra el usuario autenticado;
- OpenClaw y el LLM no acceden directamente a PostgreSQL;
- se minimiza la información enviada al proveedor del LLM;
- los logs no deben almacenar contraseñas, tokens ni credenciales;
- ante una falla del servicio de IA no debe ejecutarse ninguna modificación financiera.

### Tratamiento de la información

| Pregunta | Decisión |
|---|---|
| ¿Qué se almacena? | Usuarios (email y hash de contraseña), cuentas, movimientos y la auditoría de cada mensaje del chat. |
| ¿Qué se envía al proveedor de IA? | El mensaje, el historial de texto de la conversación y los resultados de las tools (nombres de cuentas, categorías y montos). Nunca el email, la contraseña ni el token. |
| ¿Se conserva el mensaje original? | Sí, en `audit_logs`, para trazabilidad. |
| ¿Cómo se manejan las credenciales? | Variables de entorno (`.env.example` documenta cuáles); no se versionan. |
| ¿Cómo se separan los usuarios? | El backend toma el usuario del JWT y filtra cada consulta por ese usuario. La IA no recibe ni elige el usuario. |
| ¿Qué pasa si el LLM no responde? | Ante saturación (503/429) o demora mayor a 20 segundos se reintenta una vez y se pasa a un modelo de respaldo. Si igual falla, no se modifica nada, se informa al usuario y se registra con `llm_error`. |
| ¿Qué aparece en los logs? | Mensaje, operación interpretada, decisión del backend y movimiento generado. Sin contraseñas, tokens ni API keys. |

---

## Estrategia de pruebas

La interpretación del lenguaje natural será evaluada mediante un conjunto de aproximadamente **50 a 100 expresiones representativas**.

Se incluirán casos:

- simples;
- ambiguos;
- incompletos;
- expresados de diferentes maneras.

Por ejemplo:

```text
"Gasté 5000 en nafta"
"Pagué 20 lucas de luz"
"Ayer cobré 350 mil"
"Compré una pizza"
"Gasté 12.500 con Juan"
"El martes pagué Internet"
"Anulá el último gasto"
"Me gasté unos pesos en comida"
"Pagamos 30 entre tres"
```

Para cada expresión se definirá previamente un resultado esperado:

- intención;
- monto;
- fecha;
- categoría;
- cuenta;
- información faltante;
- necesidad de aclaración;
- acción final esperada.

Una de las métricas principales será:

> **Cantidad de operaciones incorrectas ejecutadas sin solicitar aclaración al usuario.**

Además se realizarán pruebas unitarias y de integración sobre las reglas determinísticas del backend.

### Implementación

- **Set de frases:** 60 casos en [`backend/evaluacion/casos.json`](backend/evaluacion/casos.json), cada uno con su resultado esperado (`registra`, `pregunta`, `rechaza`, `consulta` o `sin_accion`).
- **Evaluación:** `python evaluacion/evaluar.py --url <backend>` envía cada frase a `POST /chat` y genera [`docs/evaluacion-nl.md`](docs/evaluacion-nl.md) con la métrica principal.
- **Resultado:** en la segunda corrida contra el despliegue, 58 de 60 casos correctos (97 %) y 1 operación incorrecta ejecutada sin aclaración. Detalle y mejoras aplicadas en [`docs/evaluacion-nl.md`](docs/evaluacion-nl.md).
- **Tests automáticos:** 42 tests con pytest (`backend/tests/`), incluidos los del chat con la IA simulada: aislamiento entre usuarios, una escritura por mensaje, monto inválido y falla del proveedor.

---

## Estructura del repositorio

```text
TP_FINAL/
├── backend/
│   ├── app/            (API, reglas de negocio, agente y chat)
│   ├── alembic/        (migraciones)
│   ├── evaluacion/     (frases de prueba y script de evaluación)
│   ├── tests/
│   └── requirements.txt
│
├── frontend/           (React + Vite)
├── openclaw/           (configuración del agente, skill y servidor MCP)
├── database/
├── docs/
│   ├── arquitectura.md
│   ├── modelo-datos.md
│   ├── modulos.md
│   ├── tools.md
│   ├── validacion-usuarios.md
│   ├── evaluacion-nl.md
│   ├── informe-final.md
│   └── guion-video.md
│
├── render.yaml         (despliegue)
└── README.md
```

### `/backend`

Contiene el backend de la aplicación y el versionado del esquema mediante Alembic.

### `/frontend`

Interfaz web desarrollada con React: login, registro, asistente (chat), cuentas, movimientos y resumen por categoría.

### `/openclaw`

Configuración del agente en OpenClaw: identidad, reglas, skill `finanzas` y un servidor MCP para pruebas desde la consola.

### `/database`

Contiene la documentación relativa a la organización y versionado de la base de datos.

El diseño se documenta en `docs/modelo-datos.md` y las migraciones se mantienen mediante Alembic dentro del backend, evitando duplicar la definición del esquema.

### `/docs`

Contiene la documentación funcional y técnica del proyecto.

---

## Documentación

La documentación principal del proyecto está dividida en los siguientes archivos:

### Modelo de datos

[`docs/modelo-datos.md`](docs/modelo-datos.md)

Define:

- entidades;
- atributos;
- tipos de datos;
- claves primarias y foráneas;
- relaciones;
- índices;
- diagrama entidad-relación;
- decisiones de diseño.

### Módulos

[`docs/modulos.md`](docs/modulos.md)

Describe los módulos funcionales del sistema y su prioridad P0, P1 o P2.

### Arquitectura

[`docs/arquitectura.md`](docs/arquitectura.md)

Describe la arquitectura general, responsabilidades de los componentes y tecnologías seleccionadas.

### Tools

[`docs/tools.md`](docs/tools.md)

Define las operaciones estructuradas mediante las cuales el agente podrá comunicarse con el backend.

### Validación con usuarios

[`docs/validacion-usuarios.md`](docs/validacion-usuarios.md)

Documenta la encuesta realizada, los resultados obtenidos y las conclusiones utilizadas para validar el problema y orientar el alcance del producto.

---

## Criterio de implementación

El desarrollo se realizará desde los componentes determinísticos hacia la capa conversacional.

El orden previsto es:

1. backend FastAPI + PostgreSQL;
2. autenticación, cuentas, movimientos y consultas;
3. definición de tools y reglas de negocio;
4. integración con OpenClaw y LLM;
5. resolución conversacional de ambigüedades;
6. interfaz web;
7. funcionalidades P1 únicamente después de estabilizar P0.

El objetivo técnico principal será completar el circuito:

```text
Mensaje
   ↓
OpenClaw + LLM
   ↓
Tool
   ↓
FastAPI
   ↓
Validación
   ↓
PostgreSQL
   ↓
Respuesta
```

---

## Instalación y ejecución local

Requisitos: Python 3.12+, Node.js 20+ y PostgreSQL.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env           # completar DATABASE_URL, JWT_SECRET_KEY y LLM_*
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

La documentación interactiva de la API queda en `http://127.0.0.1:8000/docs`.

Tests: `pytest` (usan SQLite en memoria y una IA simulada; no requieren PostgreSQL ni API key).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda en `http://localhost:5173`. En desarrollo, Vite reenvía `/api` al backend.

### Proveedor de IA

En `backend/.env`:

- **Gemini:** `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai`, `LLM_MODEL=gemini-flash-latest` y la API key de Google AI Studio.
- **OpenClaw:** ver [`openclaw/README.md`](openclaw/README.md).

---

## Despliegue

El sistema completo está desplegado en Render a partir de [`render.yaml`](render.yaml):

| Componente | URL |
|---|---|
| Aplicación web | https://finanzas-tpfinal-web.onrender.com |
| API (Swagger) | https://finanzas-tpfinal-api.onrender.com/docs |
| Base de datos | PostgreSQL administrado por Render |

Al iniciar, el backend aplica las migraciones y carga las categorías. En el plan gratuito el backend se suspende tras 15 minutos sin uso: el primer pedido puede tardar cerca de un minuto.

---

## Estado actual

Alcance P0 implementado:

- registro, inicio de sesión y aislamiento de datos por usuario;
- cuentas, categorías predefinidas, gastos e ingresos;
- anulación lógica de movimientos y desactivación de cuentas, con confirmación;
- consultas de saldo, movimientos y gastos por categoría;
- canal conversacional web (`POST /chat`) con interpretación de lenguaje natural, detección de información faltante y repreguntas;
- validaciones determinísticas en el backend;
- auditoría de cada mensaje;
- integración con OpenClaw y con Gemini;
- tests automáticos y evaluación con 60 frases;
- despliegue online.

El informe final está en [`docs/informe-final.md`](docs/informe-final.md).

---

## Equipo

- Aguilar
- Alochis
- Zupan

**Tutor:** Oscar Londero

---

## Licencia

A definir.