# Modelo de datos

## Objetivo

El modelo de datos del P0 busca representar las entidades minimas necesarias para registrar y consultar movimientos financieros personales.

Se prioriza un modelo simple que permita implementar y validar primero el nucleo funcional del sistema, evitando incorporar en esta etapa funcionalidades que aumenten innecesariamente la complejidad.

El P0 trabajara exclusivamente con pesos argentinos (ARS) y con cuentas simples de disponibilidad.

## Entidades

### User

Representa a cada usuario registrado en la aplicacion.

Campos principales:

- `id`: identificador unico.
- `email`: correo electronico utilizado para identificar al usuario.
- `password_hash`: contraseña almacenada de forma segura mediante hash.
- `created_at`: fecha y hora de creacion.

Cada usuario puede tener multiples cuentas y movimientos.

### Account

Representa una cuenta desde la cual el usuario registra ingresos y gastos.

Campos principales:

- `id`: identificador unico.
- `user_id`: usuario propietario de la cuenta.
- `name`: nombre asignado a la cuenta.
- `type`: tipo de cuenta.
- `currency`: moneda de la cuenta.
- `initial_balance`: saldo inicial informado por el usuario.
- `active`: indica si la cuenta se encuentra activa.
- `created_at`: fecha y hora de creacion.

Los tipos de cuenta contemplados inicialmente son:

- `CASH`: efectivo.
- `BANK`: cuenta bancaria.
- `WALLET`: billetera virtual.

Ejemplos:

- Efectivo.
- Banco Nacion.
- Mercado Pago.

Durante el P0 todas las cuentas utilizaran `ARS`.

No se contemplan inicialmente tarjetas de credito, inversiones ni cuentas en otras monedas.

### Category

Representa la clasificacion de un ingreso o gasto.

Campos principales:

- `id`: identificador unico.
- `name`: nombre de la categoria.
- `type`: indica si corresponde a un ingreso o gasto.

Los valores posibles para `type` son:

- `EXPENSE`
- `INCOME`

En el P0 las categorias seran predefinidas por el sistema.

Ejemplos de categorias de gastos:

- Alimentacion.
- Transporte.
- Vivienda.
- Servicios.
- Salud.
- Entretenimiento.
- Compras.
- Otros.

Ejemplos de categorias de ingresos:

- Sueldo.
- Otros ingresos.

La creacion de categorias personalizadas por parte del usuario queda fuera del alcance del P0 y podra evaluarse como funcionalidad posterior.

### Transaction

Representa un movimiento financiero registrado por el usuario.

Campos principales:

- `id`: identificador unico.
- `account_id`: cuenta asociada.
- `category_id`: categoria asociada.
- `type`: tipo de movimiento.
- `amount`: importe.
- `date`: fecha del movimiento.
- `description`: descripcion del movimiento.
- `status`: estado del movimiento.
- `created_at`: fecha y hora de creacion.
- `updated_at`: fecha y hora de ultima modificacion.

Los tipos de movimiento contemplados en P0 son:

- `EXPENSE`
- `INCOME`

Los estados iniciales son:

- `ACTIVE`
- `VOIDED`

Los movimientos no se eliminaran fisicamente como mecanismo habitual de correccion. Una operacion anulada conservara su registro y cambiara su estado a `VOIDED`, permitiendo mantener la trazabilidad.

## Relaciones

Las relaciones principales son:

- Un `User` puede tener muchas `Account`.
- Un `User` puede tener muchas `Transaction`.
- Una `Account` puede tener muchas `Transaction`.
- Una `Category` puede estar asociada a muchas `Transaction`.
- Cada `Transaction` pertenece a un unico usuario, una unica cuenta y una unica categoria.

