# Contrato de Tools — Agente ↔ Backend (v2)

Único punto de acoplamiento entre el agente (OpenClaw + LLM) y el backend FastAPI. Implementado en `backend/app/routers/agent.py` (lado backend) y `agent/tools-mcp/server.py` (lado agente, wrapper 1:1 sin reglas de negocio).

> El agente interpreta y propone. El backend valida, decide y persiste.

## 1. Convenciones

| Tema | Regla |
|---|---|
| **Identidad** | Ninguna tool recibe `user_id`. El backend toma el usuario del JWT (`Authorization: Bearer`). El LLM nunca ve ni decide el usuario. |
| **Nombres, no IDs** | El agente envía `cuenta` y `categoria_sugerida` como texto. El backend los resuelve contra las cuentas/categorías del usuario autenticado (sin tildes, sin mayúsculas, coincidencia exacta o parcial única). |
| **Monto** | Positivo, ARS, hasta 2 decimales. El agente convierte "20 lucas" → `20000`. |
| **Fechas** | `AAAA-MM-DD`, zona `America/Argentina/Buenos_Aires`. Si se omite → hoy. Fecha futura → rechazada. El agente resuelve "ayer", "este mes" con la fecha actual. |
| **Categoría** | Obligatoria en el backend. Si falta o no se reconoce → `needs_info` con las categorías válidas. |
| **Cuenta** | Obligatoria. Nunca se infiere (aunque el usuario tenga una sola). |
| **Cuenta ajena** | Se responde igual que inexistente (`ACCOUNT_NOT_FOUND`); no revela que existe. |
| **HTTP** | Las tools responden siempre `200` con envelope. Solo falta de autenticación devuelve `401/403` (el wrapper lo traduce a `UNAUTHENTICATED`). |

## 2. Envelope

```json
{
  "status": "ok | needs_info | rejected",
  "code": "string | null",
  "missing_fields": ["cuenta", "categoria"],
  "options": { "cuenta": ["Efectivo", "Mercado Pago"], "categoria": ["Alimentación", "..."] },
  "data": {},
  "message_hint": "string | null"
}
```

| `status` | Significado | Acción del agente |
|---|---|---|
| `ok` | Ejecutado / consulta resuelta. | Redacta la respuesta **solo con lo que hay en `data`**. |
| `needs_info` | Falta o es ambiguo un dato. **No se ejecutó nada.** | Pregunta solo por `missing_fields`, mostrando `options`. Luego reintenta con todos los datos. |
| `rejected` | No puede ejecutarse. | Informa el motivo; no reintenta con datos inventados. |

`needs_confirmation` queda **reservado** (no implementado en P0).

### Códigos

| Código | Status | Caso |
|---|---|---|
| `MISSING_AMOUNT` | needs_info | Monto ausente. |
| `MISSING_ACCOUNT` | needs_info | Cuenta ausente. |
| `ACCOUNT_AMBIGUOUS` | needs_info | Más de una cuenta coincide. |
| `ACCOUNT_NOT_FOUND` | needs_info | No existe o no pertenece al usuario. |
| `CATEGORY_UNRESOLVED` | needs_info | Categoría ausente o no reconocida. |
| `INVALID_AMOUNT` | rejected | ≤ 0, no numérico o > 2 decimales. |
| `INVALID_DATE` | rejected | Formato inválido o fecha futura. |
| `INVALID_TYPE` | rejected | `tipo` distinto de gasto/ingreso. |
| `RULE_VIOLATION` | rejected | Una regla de las rutas existentes rechazó la operación (detalle en `message_hint`). |
| `UNAUTHENTICATED` | rejected | Token inválido/ausente. |
| `INVALID_INPUT` | rejected | Formato de parámetros inválido (422). |
| `BACKEND_UNAVAILABLE` / `INTERNAL_ERROR` | rejected | Falla del sistema. No se modificó nada. |

Si faltan varios datos, el backend los devuelve **todos juntos** en `missing_fields` para hacer una sola pregunta.

## 3. Tools P0

| Tool | Tipo | Endpoint | Parámetros |
|---|---|---|---|
| `create_expense` | escritura | `POST /agent/expense` | `monto`, `cuenta`, `categoria_sugerida`, `fecha?`, `descripcion?` |
| `create_income` | escritura | `POST /agent/income` | ídem (`cuenta` = destino) |
| `get_balance` | lectura | `GET /agent/balance` | `cuenta?` |
| `get_transactions` | lectura | `GET /agent/transactions` | `cuenta?`, `categoria?`, `tipo?` (gasto/ingreso), `fecha_desde?`, `fecha_hasta?`, `limite?` (def. 10, máx. 50) |
| `get_expenses_by_category` | lectura | `GET /agent/expenses-by-category` | `fecha_desde?`, `fecha_hasta?`, `cuenta?`, `categoria?` |

Todos los parámetros son opcionales en el esquema del LLM: **la regla "qué es obligatorio" vive en el backend**, que responde `needs_info`. Todas las tools requieren autenticación, incluidas las de lectura.

### `data` en respuestas `ok`

- **create_expense / create_income:** `{ transaction_id, tipo, monto, cuenta, categoria, fecha, saldo_cuenta }`
- **get_balance:** `{ cuenta | null, balance, moneda }` — saldo = inicial + ingresos activos − gastos activos. Sin `cuenta` es el total.
- **get_transactions:** `{ total_resultados, movimientos: [{ id, tipo, monto, cuenta, categoria, fecha, descripcion }] }` — solo movimientos activos, más recientes primero, sin período por defecto.
- **get_expenses_by_category:** `{ periodo: {desde, hasta}, categorias: [{categoria, total}], total_gastos }` — período por defecto: mes actual.

## 4. Flujo de ejemplo

```
Usuario: "Pagué 20 lucas de luz"
Agente → create_expense(monto=20000, categoria_sugerida="servicios", descripcion="luz")
Backend → { status: "needs_info", code: "MISSING_ACCOUNT", missing_fields: ["cuenta"],
            options: { cuenta: ["Efectivo", "Mercado Pago"] } }
Agente: "Entendí $20.000 de luz. ¿Desde qué cuenta lo pagaste?"
Usuario: "Mercado Pago"
Agente → create_expense(monto=20000, cuenta="Mercado Pago", categoria_sugerida="servicios", descripcion="luz")
Backend → { status: "ok", data: { transaction_id: 142, saldo_cuenta: 231500, ... } }
```

## 5. Pendientes

- **Idempotencia:** no implementada. Un reintento puede duplicar un movimiento. Candidato a P0.5: header `Idempotency-Key` + tabla de claves.
- **Anular movimientos** (`cancel_transaction`): sin ruta en el backend; las frases de prueba "Anulá el último gasto" deben terminar en respuesta de "no disponible".
- **Confirmación** (`needs_confirmation`): reservada; definir cuándo aplica antes de implementarla.
- **Gasto compartido** ("con Juan", "pagamos 30 entre tres"): P0 lo registra entero como gasto del usuario; la descripción conserva el texto.
- **Identidad multiusuario:** el wrapper usa hoy un usuario de prueba por variables de entorno. Falta resolver cómo llega el token de cada usuario a la sesión del agente.
- **Sinónimos de categoría** ("comida" → "Alimentación"): hoy la coincidencia es por nombre; los casos no resueltos pasan por `needs_info`.

## 6. Versionado

Todo cambio en nombres, parámetros, `status` o códigos se hace primero en este documento y luego en `agent.py` y `server.py`.
