# Informe final — Plataforma Conversacional de Finanzas Personales

**Trabajo Final Integrador — Tecnicatura Universitaria en Programación (UTN)**
**Equipo:** Aguilar, Alochis, Zupan · **Tutor:** Oscar Londero
**Repositorio:** https://github.com/alochism/TP_FINAL
**Aplicación online:** https://finanzas-tpfinal-web.onrender.com

---

## 1. Introducción

El proyecto es una aplicación web para registrar y consultar gastos e ingresos personales escribiendo en lenguaje natural, por ejemplo "Pagué 20 lucas de luz con Mercado Pago", en lugar de completar un formulario.

El principio que guía todo el diseño es:

> **El agente interpreta. El backend decide.**

La inteligencia artificial solo interpreta el mensaje y propone una operación estructurada. Las validaciones, la autorización y la persistencia son responsabilidad exclusiva del backend.

---

## 2. Problema y validación

Llevar un control de las finanzas exige registrar cada movimiento con monto, fecha, categoría y cuenta. Esa carga manual genera fricción: los registros quedan incompletos o se abandonan.

Para validar el problema se encuestó a **47 personas** (detalle en [`validacion-usuarios.md`](validacion-usuarios.md)):

- 74,5 % lleva algún tipo de registro, pero solo 21,3 % lo hace de forma regular.
- 53,2 % se olvida de registrar movimientos y 42,6 % considera tedioso hacerlo.
- 91,5 % usa más de una cuenta, banco o billetera.
- 74,5 % prefiere que el sistema pregunte antes de registrar cuando falta la cuenta.
- 76,6 % usaría seguramente o probablemente una herramienta de este tipo.

**Usuario objetivo:** personas que quieren controlar sus finanzas, manejan varias cuentas o billeteras y buscan una forma más ágil que la carga manual.

Los resultados también orientaron decisiones de diseño: el sistema **pregunta la cuenta en lugar de suponerla**, y las cuentas múltiples forman parte del P0.

---

## 3. Alcance

El alcance se ordenó por prioridades siguiendo la devolución del tutor ([`modulos.md`](modulos.md)).

**P0 (implementado):** usuarios autenticados, cuentas (efectivo, banco y billetera), categorías predefinidas, gastos, ingresos, consultas de saldo, movimientos y gastos por categoría, interpretación de lenguaje natural, detección de información faltante, repreguntas, validaciones determinísticas, aislamiento entre usuarios, auditoría, interfaz web e integración con OpenClaw y un LLM.

**P1 (futuro):** transferencias internas, categorías personalizadas, recurrentes, presupuestos, múltiples monedas, tarjetas de crédito y reportes adicionales.

**P2 (futuro):** integraciones con entidades financieras, análisis avanzado y canales adicionales.

Las cuentas son **registros informativos**: la aplicación no mueve dinero real.

---

## 4. Arquitectura

```text
Usuario → Interfaz web (React) → POST /chat (FastAPI, JWT)
        → OpenClaw / LLM (interpreta y elige una tool)
        → FastAPI valida y ejecuta la tool con el usuario del JWT
        → PostgreSQL → respuesta en lenguaje natural
```

Detalle completo en [`arquitectura.md`](arquitectura.md).

### Decisiones principales

1. **La interfaz web habla solo con el backend.** El chat entra por `POST /chat` con el JWT del usuario. El backend envía el mensaje y la definición de las tools a la IA, recibe la tool elegida y la ejecuta él mismo. La IA nunca recibe ni elige el usuario, y por eso el aislamiento entre usuarios no depende del modelo.
2. **Tools con contrato fijo** ([`tools.md`](tools.md)): `create_expense`, `create_income`, `get_balance`, `get_transactions` y `get_expenses_by_category`. Responden siempre con un sobre `status` (`ok`, `needs_info`, `rejected`), `code`, `missing_fields` y `options`.
3. **Proveedor de IA reemplazable.** El backend usa el formato de Chat Completions de OpenAI. El mismo código funciona con el gateway de OpenClaw (desarrollo local) y con **Gemini Flash** en el despliegue (modelo `gemini-flash-latest`, que apunta siempre a la versión vigente). Cambiar de proveedor es cambiar tres variables de entorno.
4. **OpenClaw como orquestador** del agente: identidad, reglas y skill `finanzas`. En el despliegue se usa Gemini directo porque el gateway de OpenClaw necesita un proceso persistente que el plan gratuito de Render no ofrece.
5. **Stack acotado.** Siguiendo la devolución, se descartaron Redis, colas, jobs, Docker y canales adicionales. El contexto conversacional lo envía la interfaz como historial de texto, y las operaciones se deciden de nuevo en cada mensaje.

---

## 5. Modelo de datos

Cinco tablas en PostgreSQL, versionadas con Alembic ([`modelo-datos.md`](modelo-datos.md)):

- `users`: email y hash de la contraseña.
- `accounts`: pertenecen a un usuario; tipo `CASH`, `BANK` o `WALLET`, saldo inicial y estado activo.
- `categories`: predefinidas de gasto e ingreso.
- `transactions`: pertenecen a una cuenta; tipo, monto, fecha, descripción y estado (anulación lógica).
- `audit_logs`: una fila por mensaje del chat.

El saldo no se guarda: se calcula como *saldo inicial + ingresos activos − gastos activos*, lo que evita inconsistencias.

---

## 6. Reglas de validación y confirmación

Las reglas son determinísticas y están en el backend. No se usa un "confidence" generado por la IA para decidir.

| Situación | Decisión del backend |
|---|---|
| Monto ausente | `needs_info`: se pregunta |
| Monto ≤ 0 o con más de 2 decimales | `rejected` |
| Cuenta ausente | `needs_info`: se pregunta mostrando las cuentas del usuario |
| Cuenta inexistente, inactiva o de otro usuario | `needs_info` con `ACCOUNT_NOT_FOUND` |
| Cuenta ambigua (coincide con varias) | `needs_info` con `ACCOUNT_AMBIGUOUS` |
| Categoría no identificable | `needs_info`: se ofrecen las categorías |
| Fecha futura o inválida | `rejected` |
| Moneda distinta de ARS | `rejected` (`UNSUPPORTED_CURRENCY`) |
| Fecha no mencionada | Se registra con la fecha de hoy |
| Más de una escritura en el mismo mensaje | La segunda se rechaza (`ONE_WRITE_PER_MESSAGE`) |
| IA saturada, sin cuota o lenta (503/429/timeout) | Un reintento y, si sigue, modelo de respaldo |
| IA caída, lenta o con respuesta inválida | No se modifica nada y se informa |
| Usuario no autenticado | HTTP 401/403 |
| Anular un movimiento o desactivar una cuenta | Solo desde la interfaz, con confirmación explícita; se conserva el registro |
| Consultas | No piden confirmación, pero exigen autenticación y autorización |
| Borrar, transferir, recurrentes, presupuestos u otra moneda | No disponible en P0: el asistente lo informa y no lo simula |

Mientras falte un dato no se registra nada. Cuando el usuario responde ("Mercado Pago"), la IA vuelve a llamar a la tool con todos los datos y el backend valida otra vez.

---

## 7. Seguridad y privacidad

- Contraseñas con hash bcrypt y autenticación con JWT (60 minutos).
- Cada consulta se filtra por el usuario del token.
- Secretos en variables de entorno. Los `.env.example` documentan cuáles son, sin valores reales.
- Al proveedor de IA se envían el mensaje, el historial de texto y los resultados de las tools (nombres de cuentas, categorías y montos). Nunca el email, la contraseña ni el token.
- El mensaje original se conserva en `audit_logs` para la trazabilidad. Los logs no contienen credenciales.
- El contenido de los movimientos se trata como dato, no como instrucción: el prompt lo indica y, aunque la IA se equivocara, el backend sigue validando todo.
- **Limitación conocida:** el token se guarda en `localStorage`, y una vulnerabilidad XSS permitiría leerlo. Una mejora sería usar cookies `HttpOnly`.

---

## 8. Auditoría

Cada mensaje genera un registro con el usuario, la fecha y hora, el mensaje original, las tools que pidió la IA con sus parámetros, la decisión del backend (`status`, `code`, datos faltantes), el movimiento generado y la respuesta enviada. Ejemplo real de la prueba end-to-end:

| Mensaje | Interpretación de la IA | Decisión | Movimiento |
|---|---|---|---|
| "Pagué 20 lucas de luz" | `create_expense` · 20000 · servicios · sin cuenta | `needs_info` (`account`) | — |
| "Mercado Pago" | `create_expense` · 20000 · servicios · Mercado Pago | `ok` | #1 |

---

## 9. Pruebas

### Tests automáticos

42 tests con pytest (`backend/tests/`), sobre SQLite en memoria:

- autenticación, cuentas, movimientos y consultas;
- reglas de negocio: moneda distinta de ARS, montos inválidos, cuentas de otro usuario, categorías de tipo incorrecto, anulación de movimientos y desactivación de cuentas;
- cliente de IA: reintentos ante errores transitorios y modelo de respaldo;
- chat con la IA simulada: registro correcto, cuenta faltante, una sola escritura por mensaje, cuentas de otro usuario, monto inválido, falla del proveedor y proveedor no configurado.

### Evaluación del lenguaje natural

Se armó un set de **60 frases** ([`backend/evaluacion/casos.json`](../backend/evaluacion/casos.json)) con su resultado esperado: 20 de registro completo, 18 con datos faltantes o ambiguos, 3 inválidas, 9 consultas y 10 pedidos fuera de alcance o maliciosos. El script `backend/evaluacion/evaluar.py` las envía a `POST /chat` y compara tipo, monto, cuenta, categoría y fecha.

Métrica principal: **operaciones incorrectas ejecutadas sin solicitar aclaración**.

Resultados en [`evaluacion-nl.md`](evaluacion-nl.md).

---

## 10. Despliegue

Todo el sistema está online en Render, definido en [`render.yaml`](../render.yaml):

- PostgreSQL administrado por Render.
- Backend FastAPI: al iniciar aplica las migraciones y carga las categorías.
- Frontend estático (build de Vite).

| Componente | URL |
|---|---|
| Aplicación web | https://finanzas-tpfinal-web.onrender.com |
| API (Swagger) | https://finanzas-tpfinal-api.onrender.com/docs |

---

## 11. Respuesta a la devolución del tutor

| # | Punto de la devolución | Cómo se resolvió |
|---|---|---|
| 1 | Definir el problema | Problema, usuario objetivo y encuesta a 47 personas (sección 2) |
| 2 | Qué es una transferencia | Las cuentas son informativas; las transferencias quedan para P1 |
| 3 | Stack creciendo | Se descartaron Redis, colas, jobs, Docker y canales extra |
| 4 | Nivel del equipo | Matriz de experiencia en la propuesta del proyecto |
| 5 | Un solo canal | Solo web |
| 6 | Ambigüedades | `needs_info` con datos faltantes y opciones; repreguntas |
| 7 | No confiar en "confidence" | Reglas determinísticas en el backend (sección 6) |
| 8 | Lecturas | Sin confirmación, pero con autenticación y autorización |
| 9 | Reducir el P0 | P0/P1/P2 (sección 3) |
| 10 | Recurrentes | Fuera del P0 (P1) |
| 11 | Auditoría | Tabla `audit_logs` (sección 8) |
| 12 | Seguridad y privacidad | Sección 7 y tabla en el README |
| 13 | Proveedor y modelo | Gemini Flash (`gemini-flash-latest`), reemplazable por configuración; timeout y fallback |
| 14 | Pruebas serias de interpretación | 60 frases con resultado esperado y métrica (sección 9) |
| 15 | Prueba técnica mínima | Flujo completo mensaje → IA → tool → validación → PostgreSQL → respuesta |

---

## 12. Limitaciones y trabajo futuro

- Desde el chat no se pueden anular ni editar movimientos (sí desde la pantalla Movimientos). Se podría agregar con confirmación obligatoria.
- El historial de la conversación vive en la pestaña del navegador y se pierde al recargar.
- El plan gratuito de Render suspende el backend tras 15 minutos sin uso, y la base gratuita vence a los 30 días.
- El nivel gratuito de Gemini limita la cantidad de pedidos por minuto.
- Las funcionalidades de P1 y P2.

---

## 13. Conclusiones

El proyecto demuestra que la interpretación de lenguaje natural puede reducir la fricción del registro financiero sin entregar el control a la IA. La IA propone, pero cada operación pasa por reglas determinísticas, queda asociada al usuario autenticado y deja trazabilidad. Separar la capa de IA del dominio permitió además cambiar de proveedor sin tocar la lógica financiera.
