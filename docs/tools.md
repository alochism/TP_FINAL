# Contratos de Tools

## Objetivo

Las tools representan las operaciones estructuradas que la capa conversacional puede solicitar al backend.

OpenClaw y el modelo de lenguaje son responsables de interpretar el mensaje del usuario y determinar que operacion intenta realizar.

El backend FastAPI es responsable de validar los datos recibidos, aplicar las reglas de negocio, verificar permisos y ejecutar finalmente la operacion sobre PostgreSQL.

Principio general del sistema:

> El agente interpreta. El backend decide.

El modelo de lenguaje no accede directamente a la base de datos.


## Flujo general

El flujo esperado para una operacion conversacional es:

```text
Usuario
   |
   v
Interfaz Web
   |
   v
OpenClaw + LLM
   |
   v
Tool estructurada
   |
   v
FastAPI
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

Si falta informacion necesaria para ejecutar una operacion, el sistema debe solicitar una aclaracion antes de modificar los datos.


## Tools del P0

Durante el P0 se implementaran las siguientes tools:

- `create_expense`
- `create_income`
- `get_balance`
- `get_transactions`
- `get_expenses_by_category`


---

## create_expense

Permite registrar un gasto.

### Parametros

```json
{
  "amount": 18500,
  "date": "2026-09-23",
  "category": "Alimentacion",
  "account": "Mercado Pago",
  "description": "Compra en supermercado"
}
```

### Datos requeridos

- `amount`
- `date`
- `category`
- `account`

`description` es opcional.

### Validaciones del backend

El backend debe verificar que:

- el usuario se encuentre autenticado;
- el monto sea mayor a cero;
- la cuenta exista;
- la cuenta pertenezca al usuario autenticado;
- la cuenta se encuentre activa;
- la moneda de la cuenta sea ARS;
- la categoria exista;
- la categoria corresponda a un gasto;
- la fecha sea valida.

Si falta informacion necesaria, la operacion no debe ejecutarse.

### Resultado esperado

Si las validaciones son correctas, se registra una transaccion de tipo `EXPENSE`.

Ejemplo:

```json
{
  "success": true,
  "transaction_id": 125,
  "message": "Gasto registrado correctamente"
}
```


---

## create_income

Permite registrar un ingreso.

### Parametros

```json
{
  "amount": 350000,
  "date": "2026-09-23",
  "category": "Sueldo",
  "account": "Banco Nacion",
  "description": "Cobro de sueldo"
}
```

### Datos requeridos

- `amount`
- `date`
- `category`
- `account`

`description` es opcional.

### Validaciones del backend

El backend debe verificar que:

- el usuario se encuentre autenticado;
- el monto sea mayor a cero;
- la cuenta exista;
- la cuenta pertenezca al usuario autenticado;
- la cuenta se encuentre activa;
- la moneda de la cuenta sea ARS;
- la categoria exista;
- la categoria corresponda a un ingreso;
- la fecha sea valida.

### Resultado esperado

Si las validaciones son correctas, se registra una transaccion de tipo `INCOME`.

Ejemplo:

```json
{
  "success": true,
  "transaction_id": 126,
  "message": "Ingreso registrado correctamente"
}
```


---

## get_balance

Permite consultar el saldo disponible.

### Parametros

La consulta puede realizarse sobre una cuenta determinada.

Ejemplo:

```json
{
  "account": "Mercado Pago"
}
```

Si no se indica una cuenta, el sistema puede devolver el saldo de todas las cuentas activas del usuario.

### Validaciones del backend

El backend debe verificar que:

- el usuario se encuentre autenticado;
- la cuenta exista, cuando haya sido indicada;
- la cuenta pertenezca al usuario autenticado;
- el usuario solo pueda consultar sus propias cuentas.

### Resultado esperado

Ejemplo:

```json
{
  "account": "Mercado Pago",
  "currency": "ARS",
  "balance": 125000
}
```

El saldo se obtiene a partir del saldo inicial de la cuenta y sus movimientos activos.

Los movimientos anulados no deben afectar el saldo.


---

## get_transactions

Permite consultar los movimientos del usuario.

### Parametros

Los filtros son opcionales.

Ejemplo:

```json
{
  "date_from": "2026-09-01",
  "date_to": "2026-09-30",
  "type": "EXPENSE",
  "account": "Mercado Pago",
  "category": "Alimentacion"
}
```

### Filtros disponibles

- fecha desde;
- fecha hasta;
- tipo de movimiento;
- cuenta;
- categoria.

### Validaciones del backend

El backend debe verificar que:

- el usuario se encuentre autenticado;
- las fechas sean validas;
- la cuenta pertenezca al usuario, cuando se utilice como filtro;
- la categoria exista, cuando se utilice como filtro;
- solo se devuelvan movimientos correspondientes al usuario autenticado.

### Resultado esperado

Ejemplo:

```json
{
  "transactions": [
    {
      "id": 125,
      "type": "EXPENSE",
      "amount": 18500,
      "date": "2026-09-23",
      "category": "Alimentacion",
      "account": "Mercado Pago",
      "description": "Compra en supermercado"
    }
  ]
}
```


---

## get_expenses_by_category

Permite consultar los gastos agrupados por categoria dentro de un periodo determinado.

### Parametros

Ejemplo:

```json
{
  "date_from": "2026-09-01",
  "date_to": "2026-09-30"
}
```

Opcionalmente se puede indicar una cuenta determinada.

```json
{
  "date_from": "2026-09-01",
  "date_to": "2026-09-30",
  "account": "Mercado Pago"
}
```

### Validaciones del backend

El backend debe verificar que:

- el usuario se encuentre autenticado;
- las fechas sean validas;
- la cuenta pertenezca al usuario cuando se indique;
- solo se consideren movimientos de tipo `EXPENSE`;
- no se consideren movimientos anulados.

### Resultado esperado

Ejemplo:

```json
{
  "date_from": "2026-09-01",
  "date_to": "2026-09-30",
  "expenses": [
    {
      "category": "Alimentacion",
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
}
```


## Manejo de informacion faltante

El modelo de lenguaje puede interpretar el mensaje del usuario, pero no debe inventar informacion necesaria para ejecutar una operacion.

Por ejemplo:

> "Gaste 20 mil ayer"

Permite identificar:

- tipo: gasto;
- monto: 20000;
- fecha: ayer.

Pero pueden faltar:

- cuenta;
- categoria.

En ese caso no se debe ejecutar `create_expense`.

El sistema debe solicitar al usuario la informacion necesaria antes de continuar.

Ejemplo:

> "¿Desde que cuenta realizaste el gasto?"

Una vez obtenidos todos los datos necesarios, se puede construir la solicitud estructurada y enviarla al backend.


## Responsabilidades del backend

Las tools no reemplazan las reglas de negocio.

Aunque OpenClaw envie una solicitud estructurada correctamente, FastAPI debe volver a validar todos los datos antes de realizar cualquier modificacion.

El backend sera responsable de:

- autenticacion;
- autorizacion;
- validacion de cuentas;
- validacion de categorias;
- validacion de montos y fechas;
- separacion de datos entre usuarios;
- aplicacion de las reglas de negocio;
- persistencia de los movimientos;
- manejo de anulaciones;
- calculo de saldos;
- respuestas de error controladas.


## Alcance futuro

Las siguientes operaciones quedan fuera del P0 y podran incorporarse posteriormente:

- transferencias entre cuentas;
- movimientos recurrentes;
- presupuestos;
- categorias personalizadas;
- multiples monedas;
- tarjetas de credito;
- reportes y consultas adicionales.