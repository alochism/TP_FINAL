# Listado de módulos

## Objetivo

La Plataforma Conversacional de Finanzas Personales se organiza en módulos funcionales con responsabilidades claramente separadas.

Para ordenar el desarrollo se utilizan tres niveles de prioridad:

- `P0`: funcionalidades esenciales que conforman el producto mínimo funcional.
- `P1`: funcionalidades previstas para una segunda etapa, una vez estabilizado el núcleo del sistema.
- `P2`: funcionalidades futuras o de mayor complejidad.

El desarrollo se concentró inicialmente en implementar y validar el P0, priorizando la seguridad de las operaciones financieras, la separación de responsabilidades y la interacción mediante lenguaje natural.

---

## Módulos P0

### 1. Autenticación y usuarios

**Prioridad:** P0

Responsable de identificar a los usuarios y controlar el acceso al sistema.

Funciones implementadas:

- Registro de usuarios.
- Inicio de sesión.
- Almacenamiento seguro de contraseñas mediante hash.
- Autenticación mediante JWT.
- Identificación del usuario autenticado.
- Validación del correo electrónico.
- Validación de contraseñas durante el registro.
- Separación de la información perteneciente a distintos usuarios.

Las contraseñas deben tener al menos 8 caracteres y respetar el límite de 72 bytes en UTF-8 utilizado por el mecanismo de hash.

La identidad del usuario se determina mediante el JWT y no a partir de información interpretada por el modelo de lenguaje.

---

### 2. Gestión de cuentas

**Prioridad:** P0

Permite administrar las cuentas internas utilizadas para registrar movimientos financieros.

Tipos de cuenta implementados:

- Efectivo (`CASH`).
- Cuenta bancaria (`BANK`).
- Billetera virtual (`WALLET`).

Funciones implementadas:

- Creación de cuentas.
- Consulta de cuentas.
- Definición del saldo inicial.
- Identificación del tipo de cuenta.
- Desactivación lógica de cuentas.
- Consulta del saldo individual.
- Validación de nombres e importes iniciales.
- Prevención de nombres duplicados entre cuentas activas del mismo usuario.

Todas las cuentas utilizan pesos argentinos (`ARS`).

Los nombres de las cuentas no pueden estar vacíos ni superar los 100 caracteres. El saldo inicial no puede ser negativo y admite hasta dos decimales.

Las cuentas desactivadas conservan sus movimientos históricos, pero no pueden utilizarse para registrar nuevas operaciones.

El saldo general corresponde a las cuentas activas.

Las cuentas son registros internos del sistema y no implican conexiones reales con bancos, billeteras virtuales u otras entidades financieras.

---

### 3. Gestión de categorías

**Prioridad:** P0

Responsable de clasificar los movimientos financieros.

Las categorías se dividen en:

- Gastos (`EXPENSE`).
- Ingresos (`INCOME`).

Las categorías del P0 son predefinidas y compartidas por todos los usuarios.

Categorías de gastos:

- Alimentación.
- Transporte.
- Vivienda.
- Servicios.
- Salud.
- Educación.
- Entretenimiento.
- Compras.
- Otros.

Categorías de ingresos:

- Sueldo.
- Honorarios.
- Inversiones.
- Otros.

El backend comprueba que cada categoría exista y corresponda al tipo de movimiento que se intenta registrar.

La creación de categorías personalizadas queda fuera del P0.

---

### 4. Gestión de movimientos

**Prioridad:** P0

Constituye el núcleo financiero del sistema.

Permite registrar, consultar y anular movimientos asociados a las cuentas del usuario.

Tipos de movimientos:

- Ingresos (`INCOME`).
- Gastos (`EXPENSE`).

Funciones implementadas:

- Registro de gastos.
- Registro de ingresos.
- Asociación de movimientos a cuentas.
- Asociación de movimientos a categorías.
- Registro de importe, fecha y descripción.
- Consulta del historial de movimientos.
- Filtrado por fecha, tipo, cuenta y categoría.
- Anulación lógica de movimientos.
- Validación de reglas financieras antes de guardar operaciones.

Las validaciones principales son:

- Importe mayor que cero.
- Máximo de dos decimales.
- Importe máximo de `9999999999999.99`.
- Fechas válidas y no futuras.
- Cuenta existente, activa y perteneciente al usuario.
- Categoría válida para el tipo de movimiento.
- Operaciones exclusivamente en ARS.

Los movimientos anulados pasan del estado `ACTIVE` a `VOIDED`.

No se eliminan físicamente y dejan de afectar el cálculo de saldos y los reportes de movimientos activos.

Las validaciones compartidas de montos y fechas se encuentran centralizadas en `app/services/transaction_validation.py`.

---

### 5. Consultas financieras

**Prioridad:** P0

Permite obtener información financiera a partir de los movimientos registrados.

Funciones implementadas:

- Consulta del saldo general.
- Consulta del saldo individual de una cuenta.
- Consulta de movimientos.
- Filtrado por período.
- Filtrado por tipo de movimiento.
- Filtrado por cuenta.
- Filtrado por categoría.
- Consulta de gastos agrupados por categoría.

El saldo se calcula dinámicamente:

`Saldo = Saldo inicial + Ingresos activos - Gastos activos`

Los movimientos anulados no afectan el resultado.

El saldo general considera únicamente las cuentas activas del usuario.

Las consultas realizadas desde el asistente tienen límites de resultados para controlar la cantidad de información procesada. Por ejemplo, `get_transactions` devuelve por defecto 10 movimientos y admite hasta 50 por solicitud.

---

### 6. Procesamiento conversacional

**Prioridad:** P0

Permite que el usuario interactúe con el sistema utilizando lenguaje natural.

Ejemplos de consultas:

- "Gasté 5000 en nafta".
- "Pagué 20000 de luz".
- "Ayer cobré 350000".
- "¿Cuánto gasté este mes?"
- "¿Cuánto dinero tengo?"

El módulo utiliza Gemini para interpretar el mensaje del usuario, identificar su intención y proponer los parámetros necesarios para resolverla.

Las operaciones conversacionales disponibles son:

- `create_expense`.
- `create_income`.
- `get_balance`.
- `get_transactions`.
- `get_expenses_by_category`.

El asistente puede solicitar aclaraciones cuando faltan datos necesarios para realizar una operación.

El backend también incorpora controles para determinadas expresiones ambiguas y rechaza parámetros que no cumplen las validaciones.

El modelo de lenguaje no accede directamente a PostgreSQL ni ejecuta reglas financieras por su cuenta.

Principio de diseño:

> El agente interpreta. El backend decide.

---

### 7. Integración y orquestación conversacional

**Prioridad:** P0

La orquestación del asistente se realiza directamente desde el backend FastAPI, mediante el endpoint `POST /chat`.

El sistema utiliza Gemini a través de una API compatible con el formato de Chat Completions de OpenAI.

Responsabilidades principales:

- Recibir los mensajes enviados desde React.
- Identificar al usuario autenticado mediante JWT.
- Enviar el mensaje y el historial conversacional al proveedor de IA.
- Proporcionar al modelo las definiciones de las herramientas disponibles.
- Recibir las herramientas y los parámetros propuestos.
- Ejecutar las herramientas desde el backend.
- Procesar las respuestas de las herramientas.
- Gestionar aclaraciones y errores.
- Devolver una respuesta en lenguaje natural al usuario.

El backend permite como máximo una operación de escritura exitosa por mensaje.

La ejecución de herramientas se controla mediante resultados estructurados:

- `ok`: operación completada.
- `needs_info`: información faltante o ambigua.
- `rejected`: operación rechazada.

La integración es configurable mediante variables de entorno, lo que permite reemplazar el proveedor de IA sin modificar las reglas de negocio.

**OpenClaw y MCP** permanecen como componentes de integración alternativa en el repositorio, pero no participan del flujo principal del P0 ni son necesarios para ejecutar la aplicación web.

---

### 8. Backend y reglas de negocio

**Prioridad:** P0

Responsable de validar y ejecutar las operaciones solicitadas por la interfaz web y el asistente.

Está implementado mediante Python y FastAPI.

Responsabilidades principales:

- Autenticación y autorización.
- Validación de cuentas.
- Validación de categorías.
- Validación de importes y fechas.
- Control de propiedad de los recursos.
- Registro y anulación de movimientos.
- Consultas financieras.
- Cálculo de saldos.
- Persistencia mediante SQLAlchemy.
- Manejo de errores y respuestas controladas.
- Ejecución de herramientas solicitadas por Gemini.

El backend expone endpoints REST para las funcionalidades tradicionales y el endpoint `/chat` para la interacción conversacional.

Las operaciones REST y las herramientas del asistente comparten las reglas financieras correspondientes.

El backend constituye la autoridad final para decidir si una operación puede ejecutarse.

---

### 9. Interfaz web

**Prioridad:** P0

Proporciona el canal principal de interacción entre el usuario y el sistema.

Está desarrollada con React y se comunica con FastAPI.

Funciones implementadas:

- Registro e inicio de sesión.
- Interfaz de conversación con el asistente.
- Visualización de respuestas conversacionales.
- Consulta de cuentas y saldos.
- Creación y administración básica de cuentas.
- Registro de ingresos y gastos.
- Consulta del historial de movimientos.
- Anulación de movimientos.

El frontend no se conecta directamente con Gemini ni con PostgreSQL.

Durante el P0 se utiliza un único canal web para mantener acotado el alcance del proyecto.

Las mejoras de experiencia de usuario, como confirmaciones mediante modales propios, notificaciones visuales y ajustes de diseño responsive, forman parte de las tareas de refinamiento de la interfaz.

---

### 10. Auditoría conversacional

**Prioridad:** P0

Permite conservar información sobre las interacciones procesadas por el asistente.

Se implementa mediante la tabla `audit_logs`.

Información registrada:

- Usuario autenticado.
- Fecha y hora.
- Mensaje original.
- Herramientas solicitadas y parámetros.
- Resultado de las validaciones y decisiones del backend.
- Identificador del movimiento generado, cuando corresponde.
- Respuesta enviada al usuario.
- Indicador de error del proveedor de IA.

El objetivo es facilitar la trazabilidad del procesamiento conversacional y demostrar que las operaciones financieras están controladas por el backend.

La auditoría comprende el canal conversacional `/chat`.

No constituye un sistema de auditoría integral de todas las operaciones ejecutadas mediante los endpoints REST.

---

## Pruebas y validación del P0

Además de los módulos funcionales, el proyecto incorpora mecanismos para verificar su funcionamiento.

### Pruebas automatizadas

Se utiliza `pytest` para comprobar:

- Registro y autenticación.
- Separación de información entre usuarios.
- Creación y validación de cuentas.
- Registro de ingresos y gastos.
- Validaciones de importes y fechas.
- Anulación de movimientos.
- Cálculo de saldos.
- Consultas y reportes.
- Validación de parámetros de herramientas.
- Manejo de errores y solicitudes ambiguas.

La última ejecución realizada después de las correcciones del backend finalizó con **72 pruebas aprobadas**.

Estas pruebas utilizan un entorno controlado y, cuando corresponde, respuestas simuladas del proveedor de IA.

### Evaluación de lenguaje natural

La carpeta `backend/evaluacion/` contiene 60 consultas de prueba y un script para analizar el comportamiento conversacional del sistema utilizando Gemini.

La evaluación permite estudiar la interpretación de solicitudes, las herramientas seleccionadas y las respuestas obtenidas.

La documentación de resultados se encuentra en `docs/evaluacion-nl.md`.

Este mecanismo complementa las pruebas automatizadas, pero no las reemplaza.

---

## Módulos P1

Las siguientes funcionalidades podrán incorporarse una vez que el P0 se encuentre estable.

### Transferencias entre cuentas

**Prioridad:** P1

Permitirá registrar transferencias internas entre dos cuentas pertenecientes al mismo usuario, evitando interpretarlas como ingresos o gastos externos.

### Categorías personalizadas

**Prioridad:** P1

Permitirá que cada usuario cree y administre categorías propias para clasificar sus movimientos.

### Movimientos recurrentes

**Prioridad:** P1

Permitirá definir operaciones periódicas, como:

- Alquiler.
- Servicios.
- Suscripciones.
- Sueldo.

### Presupuestos

**Prioridad:** P1

Permitirá establecer límites de gastos por categoría o período.

### Múltiples monedas

**Prioridad:** P1

Permitirá administrar cuentas y movimientos en monedas diferentes de ARS.

Su incorporación requerirá definir reglas de conversión y cálculo de saldos.

### Tarjetas de crédito

**Prioridad:** P1

Permitirá modelar consumos, cierres, vencimientos y pagos de tarjetas.

### Reportes adicionales

**Prioridad:** P1

Incorporará consultas y visualizaciones financieras con mayor nivel de detalle.

---

## Módulos P2

### Integraciones con entidades financieras

**Prioridad:** P2

Posible integración con bancos, billeteras virtuales u otros proveedores externos para obtener movimientos automáticamente.

Esta funcionalidad dependerá de la disponibilidad, seguridad y condiciones de las APIs externas.

### Análisis financiero avanzado

**Prioridad:** P2

Podrá incorporar análisis de tendencias, comparaciones entre períodos y otras herramientas para interpretar la información financiera registrada.

---

## Resumen de prioridades

| Módulo | Prioridad |
|---|---|
| Autenticación y usuarios | P0 |
| Gestión de cuentas | P0 |
| Gestión de categorías | P0 |
| Gestión de movimientos | P0 |
| Consultas financieras | P0 |
| Procesamiento conversacional | P0 |
| Integración y orquestación conversacional | P0 |
| Backend y reglas de negocio | P0 |
| Interfaz web | P0 |
| Auditoría conversacional | P0 |
| Transferencias entre cuentas | P1 |
| Categorías personalizadas | P1 |
| Movimientos recurrentes | P1 |
| Presupuestos | P1 |
| Múltiples monedas | P1 |
| Tarjetas de crédito | P1 |
| Reportes adicionales | P1 |
| Integraciones con entidades financieras | P2 |
| Análisis financiero avanzado | P2 |

---

## Criterio de implementación

El desarrollo priorizó las funcionalidades P0, estableciendo primero las entidades financieras, las reglas de negocio y los mecanismos de autenticación.

Posteriormente se incorporó el procesamiento conversacional mediante Gemini y la ejecución controlada de herramientas desde FastAPI.

El flujo principal implementado es:

`Usuario → React → FastAPI ↔ Gemini → FastAPI ↔ PostgreSQL → React → Usuario`

La arquitectura permite que la aplicación funcione tanto mediante operaciones tradicionales de la interfaz web como mediante solicitudes expresadas en lenguaje natural.

El sistema conserva una separación clara de responsabilidades:

- React presenta la información y recibe las acciones del usuario.
- Gemini interpreta el lenguaje natural.
- FastAPI valida, autoriza y ejecuta las operaciones.
- PostgreSQL almacena la información financiera.

Las funcionalidades P1 y P2 quedan reservadas para futuras versiones, priorizando la estabilidad y la calidad del núcleo funcional implementado.

> El agente interpreta. El backend decide.