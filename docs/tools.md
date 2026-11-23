# Contratos de Tools

## Objetivo

Las tools representan las operaciones estructuradas que el asistente conversacional puede solicitar al backend de la Plataforma Conversacional de Finanzas Personales.

Durante el P0, Gemini interpreta los mensajes del usuario y propone llamadas a herramientas mediante *function calling*.

FastAPI es responsable de validar los parámetros recibidos, aplicar las reglas de negocio, verificar permisos y ejecutar las operaciones sobre PostgreSQL.

El principio general del sistema es:

> El agente interpreta. El backend decide.

El modelo de lenguaje no accede directamente a la base de datos, no determina la identidad del usuario y no ejecuta operaciones financieras por su cuenta.

---

## Flujo general

La aplicación web utiliza el siguiente flujo:

```text
Usuario
   |
   v
Interfaz Web (React)
   |
   v
FastAPI - POST /chat
   |
   v
Gemini (interpreta el mensaje)
   |
   v
Tool solicitada por Gemini
   |
   v
FastAPI (valida y ejecuta)
   |
   v
PostgreSQL
   |
   v
Respuesta al usuario
```

La definición de las herramientas y su ejecución se encuentran principalmente en:

- `app/agent/tools.py`: define las herramientas disponibles para Gemini y despacha las llamadas.
- `app/routers/tools.py`: resuelve cuentas y categorías, valida parámetros y construye las respuestas estructuradas.
- `app/routers/transactions.py` y `app/routers/accounts.py`: implementan las operaciones financieras.
- `app/services/transaction_validation.py`: centraliza las validaciones compartidas de montos y fechas.

El endpoint `/chat` invoca las funciones del backend directamente, sin realizar una segunda solicitud HTTP interna.

Los endpoints `/tools/*` también están expuestos mediante FastAPI y pueden utilizarse para pruebas e integraciones externas autenticadas.

OpenClaw y MCP permanecen como una integración alternativa, pero no son necesarios para el funcionamiento de la aplicación web del P0.

---

## Tools implementadas en el P0

El asistente dispone de cinco herramientas:

| Tool | Función |
|---|---|
| `create_expense` | Registrar un gasto |
| `create_income` | Registrar un ingreso |
| `get_balance` | Consultar saldos |
| `get_transactions` | Consultar movimientos |
| `get_expenses_by_category` | Consultar gastos agrupados por categoría |

Las operaciones de escritura son `create_expense` y `create_income`.

Las otras tres herramientas realizan consultas y no modifican los datos financieros.

---

## Formato general de respuesta

Las herramientas devuelven una estructura común denominada *envelope*.

```json
{
  "status": "ok",
  "code": null,
  "missing_fields": [],
  "options": {},
  "data": {},
  "message_hint": null
}
```

### Campos

| Campo | Descripción |
|---|---|
| `status` | Resultado general de la operación |
| `code` | Código específico de error o situación detectada |
| `missing_fields` | Datos que deben aclararse o completarse |
| `options` | Opciones disponibles para resolver una ambigüedad |
| `data` | Resultado de la operación ejecutada |
| `message_hint` | Orientación para redactar la respuesta al usuario |

Los estados posibles son:

- `ok`: operación ejecutada correctamente.
- `needs_info`: faltan datos o existe una ambigüedad que debe aclararse.
- `rejected`: la solicitud fue rechazada por una regla o validación.

En los endpoints `/tools/*`, estos estados se devuelven normalmente con HTTP 200 cuando el cuerpo de la solicitud es válido. Los errores de autenticación o validación del esquema HTTP pueden generar otros códigos, como 401, 403 o 422.

El asistente utiliza el resultado estructurado para generar una respuesta comprensible para el usuario.

---

## create_expense

Permite registrar un gasto en una cuenta del usuario autenticado.

### Parámetros

```json
{
  "amount": 18500,
  "date": "2026-09-23",
  "category": "Alimentación",
  "account": "Mercado Pago",
  "description": "Compra en supermercado",
  "currency": "ARS"
}
```

### Datos necesarios

Para registrar el gasto deben conocerse:

- `amount`: importe.
- `category`: categoría correspondiente.
- `account`: cuenta utilizada.

El parámetro `date` es opcional. Si no se informa, el backend utiliza la fecha actual de Argentina.

Los parámetros `description` y `currency` también son opcionales.

`description` admite un máximo de 200 caracteres en el contrato de la herramienta.

`currency` se utiliza cuando el usuario menciona una moneda. Si no la menciona, la operación se interpreta dentro del alcance del P0, exclusivamente en ARS.

### Validaciones del backend

El backend verifica:

- Que el usuario esté autenticado.
- Que el monto sea mayor que cero.
- Que el importe tenga como máximo dos decimales.
- Que el importe no supere `9999999999999.99`.
- Que la fecha sea válida y no sea futura.
- Que la cuenta exista, esté activa y pertenezca al usuario autenticado.
- Que la categoría exista y corresponda a un gasto.
- Que la moneda admitida sea ARS.
- Que estén disponibles todos los datos necesarios para registrar la operación.

Si el usuario menciona explícitamente otra moneda, el backend devuelve `UNSUPPORTED_CURRENCY`.

Si falta la cuenta o no se puede resolver la categoría, devuelve `needs_info` sin registrar el gasto.

### Resultado correcto

```json
{
  "status": "ok",
  "code": null,
  "missing_fields": [],
  "options": {},
  "data": {
    "success": true,
    "transaction_id": 125,
    "message": "Gasto registrado correctamente",
    "amount": 18500,
    "date": "2026-09-23",
    "account": "Mercado Pago",
    "category": "Alimentación"
  },
  "message_hint": null
}
```

---

## create_income

Permite registrar un ingreso en una cuenta del usuario autenticado.

### Parámetros

```json
{
  "amount": 350000,
  "date": "2026-09-23",
  "category": "Sueldo",
  "account": "Banco Nación",
  "description": "Cobro de sueldo"
}
```

### Datos necesarios

- `amount`: importe.
- `category`: categoría del ingreso.
- `account`: cuenta donde se registra.

La fecha es opcional y utiliza el día actual cuando no se especifica.

`description` y `currency` son opcionales.

### Validaciones del backend

Se aplican las mismas validaciones de montos, fechas, cuentas, propiedad del usuario y moneda utilizadas para los gastos.

La categoría debe existir y corresponder al tipo `INCOME`.

El backend no permite registrar el ingreso cuando falta información necesaria o se detectan parámetros inválidos.

### Resultado correcto

```json
{
  "status": "ok",
  "code": null,
  "missing_fields": [],
  "options": {},
  "data": {
    "success": true,
    "transaction_id": 126,
    "message": "Ingreso registrado correctamente",
    "amount": 350000,
    "date": "2026-09-23",
    "account": "Banco Nación",
    "category": "Sueldo"
  },
  "message_hint": null
}
```

---

## get_balance

Permite consultar el saldo registrado en una cuenta o el saldo total del usuario.

### Parámetros

El parámetro `account` es opcional.

Ejemplo de consulta individual:

```json
{
  "account": "Mercado Pago"
}
```

Si se omite, el backend devuelve el saldo total de las cuentas activas del usuario.

### Validaciones

El backend comprueba:

- Que el usuario esté autenticado.
- Que la cuenta indicada exista y esté activa.
- Que la cuenta pertenezca al usuario autenticado.
- Que una cuenta ambigua se aclare antes de ejecutar la consulta correspondiente.

### Resultado correcto

```json
{
  "status": "ok",
  "code": null,
  "missing_fields": [],
  "options": {},
  "data": {
    "account": "Mercado Pago",
    "currency": "ARS",
    "balance": 125000
  },
  "message_hint": null
}
```

Para el saldo general, `data.account` es `null`.

El saldo se calcula mediante:

`Saldo inicial + ingresos activos - gastos activos`

Los movimientos anulados (`VOIDED`) no afectan el saldo.

Las cuentas desactivadas no forman parte del saldo total de cuentas activas.

---

## get_transactions

Permite consultar los movimientos financieros registrados por el usuario.

### Parámetros

Todos los filtros son opcionales.

```json
{
  "date_from": "2026-09-01",
  "date_to": "2026-09-30",
  "type": "EXPENSE",
  "account": "Mercado Pago",
  "category": "Alimentación",
  "limit": 10
}
```

### Filtros disponibles

- `date_from`: fecha inicial.
- `date_to`: fecha final.
- `type`: `EXPENSE` o `INCOME`.
- `account`: cuenta.
- `category`: categoría.
- `limit`: cantidad máxima de movimientos solicitados.

Las fechas utilizan el formato `AAAA-MM-DD`.

Si no se indica `limit`, se utiliza el valor 10.

La herramienta devuelve como máximo 50 movimientos por consulta.

### Validaciones

El backend verifica:

- Que el usuario esté autenticado.
- Que los filtros de fecha sean válidos.
- Que el tipo de movimiento sea admitido.
- Que la cuenta indicada pertenezca al usuario.
- Que la categoría exista y pueda resolverse.
- Que solamente se consulten movimientos del usuario autenticado.

La herramienta devuelve movimientos con estado `ACTIVE`; los movimientos anulados no se incluyen en esta respuesta conversacional.

### Resultado correcto

```json
{
  "status": "ok",
  "code": null,
  "missing_fields": [],
  "options": {},
  "data": {
    "transactions": [
      {
        "id": 125,
        "type": "EXPENSE",
        "amount": 18500,
        "date": "2026-09-23",
        "category": "Alimentación",
        "account": "Mercado Pago",
        "description": "Compra en supermercado"
      }
    ]
  },
  "message_hint": null
}
```

El endpoint REST tradicional `/transactions` y esta herramienta conversacional tienen diferencias de presentación y filtrado. La herramienta aplica un límite de resultados y excluye los movimientos anulados.

---

## get_expenses_by_category

Permite consultar los gastos agrupados por categoría durante un período determinado.

### Parámetros

```json
{
  "date_from": "2026-09-01",
  "date_to": "2026-09-30",
  "account": "Mercado Pago"
}
```

Los tres parámetros son opcionales.

Si no se proporciona ninguna fecha, el backend consulta automáticamente desde el primer día del mes actual hasta la fecha de hoy.

Si se informa una cuenta, la consulta se restringe a ella.

### Validaciones

El backend verifica:

- Que el usuario esté autenticado.
- Que las fechas informadas tengan un formato válido.
- Que la cuenta indicada exista, esté activa y pertenezca al usuario.
- Que únicamente se incluyan gastos (`EXPENSE`).
- Que los movimientos estén activos (`ACTIVE`).
- Que los datos correspondan al usuario autenticado.

### Resultado correcto

```json
{
  "status": "ok",
  "code": null,
  "missing_fields": [],
  "options": {},
  "data": {
    "date_from": "2026-09-01",
    "date_to": "2026-09-30",
    "expenses": [
      {
        "category": "Alimentación",
        "amount": 85000
      },
      {
        "category": "Transporte",
        "amount": 32000
      },
      {
        "category": "Servicios",
        "amount": 45000
      }
    ]
  },
  "message_hint": null
}
```

---

## Manejo de información faltante y ambigüedades

El modelo interpreta las solicitudes del usuario, pero no debe inventar montos, cuentas o categorías.

Por ejemplo:

> Gasté 20 mil ayer.

El asistente puede interpretar:

- Tipo: gasto.
- Monto: $20.000.
- Fecha: ayer.

Pero todavía faltan la cuenta y la categoría.

En ese caso, la operación no se registra.

El backend puede devolver:

```json
{
  "status": "needs_info",
  "code": "MISSING_ACCOUNT",
  "missing_fields": [
    "account",
    "category"
  ],
  "options": {
    "account": [
      "Efectivo",
      "Mercado Pago"
    ],
    "category": [
      "Alimentación",
      "Transporte",
      "Servicios",
      "Otros"
    ]
  },
  "data": {},
  "message_hint": "No se registro nada. Pedi al usuario solo los datos faltantes."
}
```

Las opciones del ejemplo son ilustrativas; las respuestas reales se construyen con las cuentas y categorías disponibles en el sistema.

Gemini utiliza esta información para formular una pregunta al usuario.

Cuando recibe la aclaración, puede solicitar nuevamente la herramienta con los datos completos.

### Categorías ambiguas

El asistente no debe asignar automáticamente una categoría cuando el motivo del gasto es insuficiente.

Por ejemplo:

> Gasté 3000 en algo con efectivo.

El backend incorpora una protección para determinadas expresiones vagas y solicita aclaración antes de registrar el movimiento.

Si el usuario responde:

> Ponelo en Otros.

La operación puede completarse utilizando la categoría indicada.

Esta protección contempla patrones de ambigüedad conocidos; no garantiza detectar todas las interpretaciones semánticas incorrectas que pueda generar el modelo.

---

## Manejo de errores

Las herramientas utilizan códigos específicos para identificar situaciones que impiden completar una operación.

Entre ellos:

| Código | Significado |
|---|---|
| `MISSING_AMOUNT` | No se informó un monto |
| `MISSING_ACCOUNT` | No se informó una cuenta |
| `ACCOUNT_NOT_FOUND` | No se encontró la cuenta indicada |
| `ACCOUNT_AMBIGUOUS` | La referencia de cuenta no es inequívoca |
| `CATEGORY_UNRESOLVED` | No se pudo resolver la categoría |
| `INVALID_AMOUNT` | Monto inválido o fuera de los límites admitidos |
| `INVALID_DATE` | Fecha inválida o futura |
| `UNSUPPORTED_CURRENCY` | Moneda distinta de ARS |
| `INVALID_TYPE` | Tipo de movimiento no admitido |
| `RULE_VIOLATION` | Una regla de negocio impidió ejecutar la operación |
| `INVALID_INPUT` | Parámetros enviados por el modelo incorrectos |
| `ONE_WRITE_PER_MESSAGE` | Se intentó ejecutar otra escritura luego de una escritura exitosa en el mismo mensaje |
| `UNKNOWN_TOOL` | Se solicitó una herramienta no disponible |

Los códigos son utilizados internamente. El asistente debe explicar el problema en lenguaje natural, sin exponer detalles técnicos innecesarios.

Ante parámetros inválidos, el backend rechaza la operación sin registrar movimientos.

Si el proveedor de IA presenta un error, `/chat` devuelve una respuesta controlada. Cuando una escritura ya fue confirmada antes del error, el sistema conserva el movimiento y lo informa al usuario.

---

## Responsabilidades del backend

Las tools no reemplazan las reglas de negocio.

Aunque Gemini envíe parámetros estructurados, FastAPI debe validar la operación antes de ejecutarla.

El backend es responsable de:

- Autenticación mediante JWT.
- Autorización por usuario.
- Validación de cuentas activas y propiedad.
- Validación de categorías.
- Validación de importes y fechas.
- Restricción a operaciones en ARS.
- Manejo de información faltante y ambigüedades detectadas.
- Separación de los datos financieros entre usuarios.
- Persistencia de movimientos.
- Cálculo de saldos.
- Consultas y reportes.
- Respuestas de error controladas.

Además, el endpoint `/chat` limita a una operación de escritura exitosa por mensaje.

La anulación de movimientos y la desactivación de cuentas se encuentran disponibles mediante endpoints REST y la interfaz web, pero no forman parte de las cinco herramientas conversacionales del P0.

---

## Pruebas y validación

El sistema utiliza dos mecanismos complementarios.

**Pruebas automatizadas con pytest**

Comprueban autenticación, autorización, reglas de negocio, herramientas, errores y operaciones financieras utilizando un entorno de pruebas controlado.

**Evaluación de lenguaje natural**

La carpeta `backend/evaluacion/` contiene un conjunto de 60 frases y un script para medir el comportamiento del asistente utilizando un proveedor real de IA.

Estas evaluaciones permiten analizar tanto la ejecución técnica de las operaciones como la interpretación de mensajes cotidianos.

Los resultados documentados de las corridas se encuentran en `docs/evaluacion-nl.md`.

---

## Alcance futuro

Quedan fuera de las herramientas conversacionales del P0:

- Transferencias entre cuentas.
- Movimientos recurrentes.
- Presupuestos.
- Categorías personalizadas.
- Múltiples monedas.
- Tarjetas de crédito.
- Anulación o edición de movimientos mediante conversación.
- Integraciones directas con bancos o billeteras.
- Herramientas adicionales para reportes avanzados.

La arquitectura permite incorporar nuevas operaciones manteniendo separadas la interpretación del lenguaje natural y la ejecución de las reglas financieras.