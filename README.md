# Plataforma Conversacional de Finanzas Personales

Asistente financiero personal que permite registrar y consultar ingresos, gastos, presupuestos, transferencias y pagos recurrentes enviando **mensajes en lenguaje natural**, mientras un backend propio mantiene el modelo financiero estructurado, validado y consistente.

> El agente de IA interpreta. El backend decide.

## Idea general

En lugar de completar formularios, el usuario escribe algo como:

```
"Gasté 12.500 en una pizza con Juan"
```

Un agente de IA interpreta el mensaje y lo convierte en un comando estructurado (monto, categoría, fecha, tipo, nivel de confianza). Ese comando pasa por validación de esquema y de reglas de negocio antes de ejecutarse contra los servicios de dominio del backend, que son la única autoridad para decidir si la operación es válida y persistirla.

El LLM **no** accede a la base de datos ni contiene lógica de negocio: solo interpreta lenguaje natural y llama a funciones (*tools*) expuestas por el backend — crear una transacción, transferir entre cuentas, consultar balance, generar un resumen. Cuando la interpretación es ambigua o de baja confianza, el sistema no asume: guarda un borrador y le pregunta al usuario.

```
Canal (WhatsApp / Telegram / Web)
        ↓
     Gateway
        ↓
   Agente de IA (interpreta) → comando estructurado
        ↓
  Validación (schema + reglas de negocio)
        ↓
   Autorización + Idempotencia
        ↓
   Servicios de dominio (backend)
        ↓
     PostgreSQL (transacción ACID)
```

## Funcionalidades principales

- Registro de ingresos y gastos por lenguaje natural.
- Consultas conversacionales: balance, gastos por categoría, resumen mensual.
- Manejo de confianza y confirmación explícita ante datos ambiguos.
- Cuentas múltiples (efectivo, banco, billetera virtual) y transferencias entre ellas.
- Presupuestos por categoría con seguimiento y alertas.
- Transacciones recurrentes (suscripciones, pagos fijos) vía jobs en segundo plano.
- Registro de auditoría de todas las operaciones.
- Dashboard web liviano de solo administración/visualización.

## Stack tecnológico

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend | Python + FastAPI | Validación con Pydantic, tipado, buen soporte de SDKs de LLM y tool calling |
| Base de datos | PostgreSQL | Integridad referencial, transacciones ACID, agregaciones — clave para datos financieros |
| Cache / colas | Redis | Estado de conversación, rate limiting, broker de jobs en segundo plano |
| Frontend | Node.js + React | Dashboard liviano de administración, consume la misma API REST |
| Orquestación | OpenClaw | Integra canal de mensajería, agente de IA y backend, sin alojar lógica de negocio |
| Migraciones | Alembic | Versionado de schema de base de datos |
| Testing | pytest | Tests de integración sobre API y servicios de dominio |
| Deploy | Docker Compose (VPS) o Railway/Render | A definir en etapa de hardening |

## Arquitectura del código

```
api/            # routers FastAPI, capa HTTP
services/       # lógica de negocio / dominio (la única autoridad)
repositories/   # acceso a datos (SQLAlchemy)
models/         # entidades ORM
ai/             # prompts, definición de tools, parsing/validación de salidas del LLM
jobs/           # tareas en segundo plano (recurrentes, notificaciones)
web/            # dashboard (Node/React)
tests/
```

## Principios de diseño

- El LLM nunca escribe directo en la base de datos.
- Toda mutación pasa por: validación de schema → validación de negocio → autorización → idempotencia → transacción DB.
- Operaciones de lectura se ejecutan directo; operaciones sensibles (borrar, transferir) requieren confirmación explícita del usuario.
- El sistema debe seguir siendo consistente aunque el LLM falle, tarde o devuelva una respuesta inválida.

## Estado del proyecto

Proyecto final de Tecnicatura en Programación (orientación Desarrollo Web). En desarrollo — ver [`plan-tecnico.md`](./plan-tecnico.md) para el roadmap mes a mes.

## Licencia

A definir.
