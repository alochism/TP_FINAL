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
| Contenedores | Docker | Entorno reproducible |
| Control de versiones | Git + GitHub | Versionado y colaboración |

El proveedor de LLM y el servicio de despliegue se definirán durante la implementación en función de compatibilidad, costo y requisitos técnicos.

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

---

## Estructura del repositorio

```text
TP_FINAL/
├── backend/
│   ├── app/
│   ├── alembic/
│   └── requirements.txt
│
├── database/
│   └── README.md
│
├── docs/
│   ├── images/
│   ├── arquitectura.md
│   ├── modelo-datos.md
│   ├── modulos.md
│   ├── tools.md
│   └── validacion-usuarios.md
│
├── frontend/
│
└── README.md
```

### `/backend`

Contiene el backend de la aplicación y el versionado del esquema mediante Alembic.

### `/frontend`

Reservado para la interfaz web desarrollada con React.

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

## Estado actual

El proyecto se encuentra en desarrollo dentro del marco del **Trabajo Final de la Tecnicatura Universitaria en Programación**.

Actualmente se encuentran definidos:

- problema y usuario objetivo;
- validación inicial con usuarios;
- alcance P0, P1 y P2;
- arquitectura general;
- módulos funcionales;
- modelo de datos;
- tecnologías principales;
- contratos iniciales de tools;
- criterios de seguridad;
- estrategia inicial de pruebas;
- estructura del repositorio.

La documentación se actualizará progresivamente a medida que avance la implementación y se incorporen las devoluciones del tutor.

---

## Equipo

- Aguilar
- Alochis
- Zupan

**Tutor:** Oscar Londero

---

## Licencia

A definir.