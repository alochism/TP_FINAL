# Listado de modulos

## Objetivo

El sistema se organiza en modulos funcionales con responsabilidades claramente separadas.

Para ordenar el desarrollo se utilizan tres niveles de prioridad:

- `P0`: funcionalidades esenciales para disponer de un producto minimo funcional.
- `P1`: funcionalidades previstas para una segunda etapa, una vez estabilizado el nucleo del sistema.
- `P2`: funcionalidades futuras o de mayor complejidad.

El objetivo inicial es completar y validar el alcance P0 antes de incorporar funcionalidades adicionales.

---

## Modulos P0

### 1. Autenticacion y usuarios

**Prioridad:** P0

Responsable de identificar a los usuarios y controlar el acceso al sistema.

Funciones principales:

- Registro de usuarios.
- Inicio de sesion.
- Almacenamiento seguro de contraseñas mediante hash.
- Autenticacion mediante token.
- Identificacion del usuario autenticado.
- Separacion de la informacion perteneciente a distintos usuarios.

---

### 2. Gestion de cuentas

**Prioridad:** P0

Permite administrar las cuentas internas utilizadas para registrar los movimientos financieros del usuario.

Tipos de cuenta contemplados inicialmente:

- Efectivo (`CASH`).
- Cuenta bancaria (`BANK`).
- Billetera virtual (`WALLET`).

Funciones principales:

- Creacion de cuentas.
- Consulta de cuentas.
- Definicion de saldo inicial.
- Identificacion del tipo de cuenta.
- Activacion o desactivacion logica de cuentas.
- Consulta del saldo.

Durante el P0 todas las cuentas utilizan pesos argentinos (`ARS`).

Las cuentas son registros internos del sistema y no implican una conexion directa con bancos, billeteras virtuales u otras entidades financieras.

---

### 3. Gestion de categorias

**Prioridad:** P0

Responsable de clasificar los movimientos financieros.

Las categorias se dividen en:

- Categorias de gastos (`EXPENSE`).
- Categorias de ingresos (`INCOME`).

En el P0 las categorias son predefinidas por el sistema.

Ejemplos:

- Alimentacion.
- Transporte.
- Vivienda.
- Servicios.
- Salud.
- Educacion.
- Entretenimiento.
- Compras.
- Sueldo.
- Honorarios.
- Otros.

---

### 4. Gestion de movimientos

**Prioridad:** P0

Es el nucleo financiero del sistema.

Permite registrar y consultar los movimientos asociados a las cuentas del usuario.

Tipos de movimientos:

- Ingresos (`INCOME`).
- Gastos (`EXPENSE`).

Funciones principales:

- Registro de gastos.
- Registro de ingresos.
- Asociacion del movimiento a una cuenta.
- Asociacion del movimiento a una categoria.
- Registro de importe, fecha y descripcion.
- Consulta del historial de movimientos.
- Filtrado por fecha, tipo, cuenta y categoria.
- Anulacion logica de movimientos.

Los movimientos anulados no se eliminan fisicamente. Se conserva el registro para mantener la trazabilidad de las operaciones.

---

### 5. Consultas financieras

**Prioridad:** P0

Permite obtener informacion financiera a partir de los movimientos registrados.

Funciones principales:

- Consulta del saldo general.
- Consulta del saldo de una cuenta.
- Consulta de movimientos.
- Filtrado de movimientos por periodo.
- Filtrado por tipo de movimiento.
- Filtrado por cuenta.
- Filtrado por categoria.
- Consulta de gastos agrupados por categoria.

El saldo se calcula a partir del saldo inicial de las cuentas y los movimientos activos registrados.

---

### 6. Procesamiento conversacional

**Prioridad:** P0

Permite que el usuario interactue con el sistema utilizando lenguaje natural.

Ejemplos:

- "Gaste 5000 en nafta".
- "Pague 20000 de luz".
- "Ayer cobre 350000".
- "Cuanto gaste este mes?"
- "Cuanto dinero tengo?"

El modulo conversacional interpreta el mensaje y determina la intencion y los datos proporcionados por el usuario.

Cuando falte informacion necesaria para ejecutar una operacion, el sistema debera solicitar una aclaracion antes de realizarla.

El agente no accede directamente a la base de datos ni ejecuta reglas financieras por su cuenta.

Principio de diseño:

> El agente interpreta. El backend decide.

---

### 7. Orquestacion del agente

**Prioridad:** P0

OpenClaw sera utilizado como capa de orquestacion entre la interfaz conversacional, el modelo de lenguaje y el backend.

Responsabilidades principales:

- Recibir el mensaje del usuario.
- Coordinar la interaccion con el modelo de lenguaje.
- Identificar la herramienta necesaria para resolver la solicitud.
- Enviar solicitudes estructuradas al backend.
- Gestionar las aclaraciones necesarias.
- Presentar al usuario la respuesta obtenida.

OpenClaw no contiene las reglas de negocio financieras ni accede directamente a PostgreSQL.

---

### 8. Backend y reglas de negocio

**Prioridad:** P0

Responsable de validar y ejecutar las operaciones solicitadas por los distintos clientes del sistema.

Se implementara mediante una API REST.

Responsabilidades principales:

- Autenticacion y autorizacion.
- Validacion de cuentas.
- Validacion de categorias.
- Validacion de importes y fechas.
- Control de propiedad de los recursos.
- Registro de movimientos.
- Consulta de informacion financiera.
- Calculo de saldos.
- Persistencia de datos.
- Manejo controlado de errores.

El backend constituye la autoridad final para decidir si una operacion puede ejecutarse.

---

### 9. Interfaz web

**Prioridad:** P0

Proporciona el canal de interaccion entre el usuario y el sistema.

Funciones principales:

- Registro e inicio de sesion.
- Interfaz conversacional.
- Visualizacion de respuestas.
- Consulta basica de informacion financiera.
- Gestion basica de cuentas.

Se utilizara un unico canal web durante el P0 para mantener acotado el alcance del proyecto.

---

## Modulos P1

Las siguientes funcionalidades podran incorporarse una vez que el P0 se encuentre estable.

### Transferencias entre cuentas

Permitira registrar movimientos internos entre dos cuentas pertenecientes al mismo usuario.

**Prioridad:** P1

### Categorias personalizadas

Permitira que cada usuario cree y administre sus propias categorias.

**Prioridad:** P1

### Movimientos recurrentes

Permitira definir operaciones que se repitan periodicamente.

Ejemplos:

- Alquiler.
- Servicios.
- Suscripciones.
- Sueldo.

**Prioridad:** P1

### Presupuestos

Permitira establecer limites de gasto por categoria o periodo.

**Prioridad:** P1

### Multiples monedas

Permitira administrar cuentas y movimientos en monedas distintas de ARS.

**Prioridad:** P1

### Tarjetas de credito

Permitira modelar consumos, cierres y pagos de tarjetas de credito.

**Prioridad:** P1

### Reportes adicionales

Incorporara consultas y visualizaciones financieras de mayor detalle.

**Prioridad:** P1

---

## Modulos P2

### Integraciones con entidades financieras

Posible integracion futura con bancos, billeteras virtuales u otros proveedores externos para obtener movimientos automaticamente.

**Prioridad:** P2

Esta funcionalidad no forma parte del alcance inicial y dependera de la disponibilidad, seguridad y condiciones de las APIs externas.

### Analisis financiero avanzado

Podra incorporar analisis de tendencias, comparaciones entre periodos y otras herramientas de apoyo para interpretar la informacion financiera registrada.

**Prioridad:** P2

---

## Resumen de prioridades

| Modulo | Prioridad |
|---|---|
| Autenticacion y usuarios | P0 |
| Gestion de cuentas | P0 |
| Gestion de categorias | P0 |
| Gestion de movimientos | P0 |
| Consultas financieras | P0 |
| Procesamiento conversacional | P0 |
| Orquestacion del agente | P0 |
| Backend y reglas de negocio | P0 |
| Interfaz web | P0 |
| Transferencias entre cuentas | P1 |
| Categorias personalizadas | P1 |
| Movimientos recurrentes | P1 |
| Presupuestos | P1 |
| Multiples monedas | P1 |
| Tarjetas de credito | P1 |
| Reportes adicionales | P1 |
| Integraciones con entidades financieras | P2 |
| Analisis financiero avanzado | P2 |

---

## Criterio de implementacion

El desarrollo se realizara priorizando los modulos P0.

La primera version funcional debera permitir completar el flujo principal:

`Usuario → Interfaz web → OpenClaw → Agente/LLM → Backend → PostgreSQL → Respuesta`

Las funcionalidades P1 y P2 se incorporaran solamente una vez que el flujo principal se encuentre validado y estable, evitando aumentar la complejidad del sistema antes de comprobar el funcionamiento de su nucleo.