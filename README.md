# Plataforma Conversacional de Finanzas Personales

Asistente financiero personal que permite registrar y consultar gastos e ingresos mediante lenguaje natural a través de una interfaz conversacional, utilizando **OpenClaw como capa de orquestación del agente de IA** y un backend propio como única autoridad sobre las reglas de negocio, la autorización y la persistencia de la información.

> **El agente interpreta. El backend decide.**

## Problema

El control cotidiano de las finanzas personales requiere registrar de manera frecuente gastos e ingresos. Sin embargo, muchas de las herramientas disponibles requieren que el usuario complete manualmente formularios indicando monto, fecha, categoría, cuenta y descripción para cada movimiento.

El proyecto parte de la hipótesis de que esta fricción puede provocar que algunas personas registren sus movimientos de manera incompleta, irregular o directamente abandonen el seguimiento de sus finanzas personales.

La propuesta busca evaluar si una interfaz conversacional basada en lenguaje natural puede reducir esa fricción, permitiendo registrar y consultar movimientos mediante expresiones cotidianas como:

> "Gasté 18.500 en supermercado con la Visa."

en lugar de completar manualmente cada uno de los campos de un formulario tradicional.

## Usuario objetivo

El producto está orientado inicialmente a personas que desean llevar un control de sus finanzas personales mediante el registro de sus ingresos y gastos, pero buscan una alternativa más ágil que la carga manual mediante formularios tradicionales.

Como hipótesis inicial, se consideran potenciales usuarios aquellas personas que actualmente:

- utilizan planillas, notas, aplicaciones financieras u otros mecanismos manuales para registrar sus movimientos;
- realizan el registro de manera irregular;
- abandonaron anteriormente alguna herramienta de seguimiento financiero por resultar poco práctica o tediosa;
- o directamente no llevan un registro sistemático de sus finanzas personales.

El proyecto propone reducir la cantidad de pasos necesarios para registrar y consultar información financiera mediante una interacción basada en lenguaje natural.

Esta definición inicial del usuario objetivo será validada mediante entrevistas con potenciales usuarios antes de cerrar definitivamente el alcance funcional del producto.

## Validación del problema

La hipótesis inicial del proyecto será validada mediante entrevistas breves con potenciales usuarios antes de cerrar definitivamente el alcance funcional.

Las entrevistas buscarán conocer principalmente:

- si actualmente registran sus ingresos y gastos;
- qué herramientas utilizan para hacerlo (aplicaciones, planillas, notas u otros métodos);
- con qué frecuencia realizan el registro;
- qué dificultades encuentran durante la carga de movimientos;
- si utilizaron anteriormente aplicaciones de finanzas personales y, en caso de haberlas abandonado, cuáles fueron los motivos;
- qué información consideran importante consultar sobre sus finanzas;
- si una interacción mediante lenguaje natural les resultaría más práctica que completar formularios tradicionales.

Los resultados obtenidos se utilizarán para validar o ajustar la definición del problema, el usuario objetivo y las funcionalidades priorizadas para el MVP.

**Estado:** validación con usuarios pendiente.

## Idea general

En lugar de completar manualmente un formulario para registrar cada movimiento, el usuario podrá interactuar con el sistema mediante lenguaje natural.

Por ejemplo:

> "Gasté 12.500 en una pizza con Juan."

La interacción será procesada por **OpenClaw**, utilizado como capa de orquestación del agente conversacional. OpenClaw gestionará la interacción con el modelo de lenguaje y permitirá que el agente interprete el mensaje y genere una solicitud estructurada para las operaciones disponibles en el backend.

Una posible interpretación del mensaje anterior sería:

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

Esta interpretación no implica que la operación pueda ejecutarse.

El backend recibe la solicitud estructurada y aplica las validaciones de esquema, autenticación, autorización y reglas de negocio correspondientes.

Si falta información obligatoria, el sistema no debe asumirla. Por ejemplo, si no pudo determinar desde qué cuenta se realizó el gasto:

> "Entendí que gastaste $12.500 en alimentación. ¿Desde qué cuenta lo pagaste?"

Una vez obtenida y validada toda la información necesaria, el backend ejecuta la operación y la persiste en PostgreSQL.

El flujo general será:

```text
Usuario
   ↓
Interfaz web
   ↓
OpenClaw
   ↓
Agente / LLM
   ↓
Tool / comando estructurado
   ↓
Backend (FastAPI)
   ↓
Validación + autorización + reglas de negocio
   ↓
PostgreSQL
   ↓
Respuesta al usuario
```

OpenClaw y el modelo de lenguaje forman parte de la capa de interpretación y orquestación. No acceden directamente a PostgreSQL ni contienen las reglas financieras del sistema.

> **El agente interpreta. El backend decide.**

## Rol de OpenClaw

**OpenClaw** será utilizado como capa de orquestación del agente conversacional. Su función será gestionar la interacción entre el usuario, el modelo de lenguaje y las herramientas (*tools*) disponibles para comunicarse con el backend.

Dentro de la arquitectura del proyecto, OpenClaw será responsable de:

- gestionar la interacción con el modelo de lenguaje;
- mantener el contexto necesario de la conversación;
- permitir que el agente determine qué herramienta debe utilizar según la intención del usuario;
- invocar las *tools* disponibles para solicitar operaciones al backend;
- facilitar la incorporación futura de otros canales conversacionales, como WhatsApp o Telegram.

Las *tools* representarán operaciones controladas que el agente puede solicitar, por ejemplo:

```text
create_expense(...)
create_income(...)
get_balance(...)
get_transactions(...)
get_expenses_by_category(...)
```

La ejecución real de estas operaciones estará implementada en el backend. OpenClaw no tendrá acceso directo a PostgreSQL ni será responsable de validar las reglas financieras del sistema.

Por ejemplo:

```text
Usuario:
"Gasté $18.500 en supermercado con la Visa"
        ↓
OpenClaw + LLM:
interpreta la intención y selecciona create_expense(...)
        ↓
Backend:
valida usuario, cuenta, monto, categoría y reglas de negocio
        ↓
PostgreSQL:
persiste el movimiento
        ↓
Backend:
devuelve el resultado
        ↓
OpenClaw:
genera la respuesta conversacional al usuario
```

Esta separación busca desacoplar la capa conversacional de la lógica financiera. De esta manera, OpenClaw se ocupa de la orquestación del agente, mientras que el backend mantiene el control sobre las operaciones y la consistencia de los datos.

## Comandos estructurados y tools

La comunicación entre la capa conversacional y el backend se realizará mediante **tools con entradas estructuradas y previamente definidas**.

El agente gestionado mediante OpenClaw podrá interpretar la intención expresada por el usuario y seleccionar la tool correspondiente, pero no podrá ejecutar operaciones financieras directamente sobre la base de datos.

Para el alcance P0 se contemplan inicialmente tools como:

```text
create_expense(...)
create_income(...)
get_balance(...)
get_transactions(...)
get_expenses_by_category(...)
```

Por ejemplo, ante el mensaje:

> "Gasté ayer $18.500 en supermercado con la Visa."

el agente podrá seleccionar `create_expense` y generar una entrada estructurada similar a:

```json
{
  "amount": 18500,
  "currency": "ARS",
  "date": "2026-08-20",
  "suggested_category": "supermercado",
  "account": "Visa",
  "description": "compra en supermercado"
}
```

Esta estructura representa una **solicitud de operación**, no una operación ya autorizada.

El backend será responsable de validar, entre otras cosas:

- que el usuario esté autenticado;
- que los campos obligatorios estén presentes;
- que los tipos y formatos recibidos sean válidos;
- que el monto sea válido;
- que la cuenta indicada exista y pertenezca al usuario autenticado;
- que la categoría exista o pueda resolverse de forma segura;
- que la operación solicitada esté permitida;
- y que se cumplan las reglas de negocio correspondientes.

Si falta información necesaria o existe una ambigüedad que impide ejecutar la operación de forma segura, el backend no realizará ninguna modificación y la capa conversacional deberá solicitar la información faltante al usuario.

Por ejemplo:

```text
Usuario:
"Gasté 20.000 ayer"

Agente:
detecta monto y fecha, pero no puede determinar la cuenta

Backend:
indica que falta un dato obligatorio

Sistema:
"¿Desde qué cuenta realizaste el gasto?"
```

De esta forma, las salidas generadas por el modelo funcionan como datos de entrada para el sistema, pero nunca reemplazan las validaciones determinísticas ni las reglas de negocio implementadas en el backend.

## Validación: no solo `confidence`

El nivel de confianza (`confidence`) generado durante la interpretación del mensaje podrá utilizarse como una señal auxiliar, pero no determinará por sí solo si una operación puede ejecutarse.

La decisión final dependerá siempre de reglas determinísticas implementadas en el backend.

Entre las validaciones iniciales se contemplan:

- monto obligatorio ausente → solicitar al usuario;
- monto inválido → rechazar la operación;
- cuenta obligatoria ausente → solicitar al usuario;
- cuenta inexistente → solicitar corrección;
- cuenta perteneciente a otro usuario → rechazar la operación;
- categoría dudosa o no identificada → sugerir o solicitar confirmación, sin asumir;
- información contradictoria → no ejecutar hasta resolver la ambigüedad;
- operación destructiva, como eliminar un movimiento → requerir confirmación explícita;
- usuario no autenticado → rechazar la operación;
- usuario no autorizado para acceder al recurso → rechazar la operación.

Por ejemplo:

> "Gasté 15.000 en el supermercado."

Aunque el agente tenga un nivel alto de confianza respecto del monto y la categoría, si el sistema requiere conocer desde qué cuenta se realizó el gasto y esa información no está disponible, la operación no será registrada hasta obtenerla.

Del mismo modo, un valor bajo de `confidence` no implica automáticamente rechazar una operación. El backend evaluará qué información concreta falta o resulta ambigua y solicitará al usuario únicamente las aclaraciones necesarias.

Las operaciones de consulta no requerirán una confirmación adicional, pero estarán sujetas a los mismos mecanismos de autenticación y autorización que las operaciones de escritura.

De esta forma, `confidence` funciona como información complementaria de la interpretación del agente, mientras que la seguridad y consistencia del sistema dependen de reglas explícitas y verificables implementadas en el backend.

## Alcance del MVP (P0 / P1 / P2)

El desarrollo se organizará por niveles de prioridad para garantizar que el núcleo del producto pueda completarse, probarse y desplegarse antes de incorporar funcionalidades adicionales.

### P0 — Núcleo obligatorio

Corresponde al alcance mínimo que deberá estar completamente funcional para la entrega y defensa del proyecto.

- Registro e inicio de sesión de usuarios.
- Gestión básica de cuentas.
- Registro de gastos mediante lenguaje natural.
- Registro de ingresos mediante lenguaje natural.
- Consulta de saldo de las cuentas registradas.
- Consulta de movimientos.
- Consulta de gastos por categoría.
- Detección de información obligatoria faltante.
- Interacción conversacional para completar información ambigua.
- Confirmación explícita cuando corresponda.
- Validación de todas las operaciones mediante reglas determinísticas del backend.
- Auditoría básica de las interacciones y operaciones.
- Interfaz web como único canal de interacción del MVP.
- Integración de OpenClaw como capa de orquestación del agente conversacional.

El objetivo de P0 es demostrar de punta a punta el circuito principal del producto:

```text
Usuario
   ↓
Interfaz web
   ↓
OpenClaw + LLM
   ↓
Tool / solicitud estructurada
   ↓
Backend
   ↓
Validación + reglas de negocio
   ↓
PostgreSQL
   ↓
Respuesta al usuario
```

### P1 — Ampliaciones

Una vez completado y validado P0, podrán incorporarse:

- transferencias internas entre cuentas registradas en la aplicación;
- presupuestos por categoría;
- movimientos recurrentes;
- mecanismos simples de notificación.

### P2 — Funcionalidades opcionales

Si el tiempo y la estabilidad del proyecto lo permiten, podrán evaluarse:

- alertas y reportes avanzados;
- integración con canales adicionales como WhatsApp o Telegram;
- dashboard con visualizaciones y estadísticas más completas;
- automatizaciones adicionales;
- incorporación de infraestructura complementaria cuando exista una necesidad técnica concreta.

Las funcionalidades P1 y P2 no condicionan el funcionamiento del núcleo del producto ni serán necesarias para considerar completo el MVP.

## Alcance de las cuentas y operaciones financieras

Las cuentas utilizadas dentro de la plataforma son **representaciones informativas creadas por el usuario** para organizar y registrar sus finanzas personales.

La aplicación **no tendrá integración con bancos, billeteras virtuales, tarjetas de crédito, procesadores de pago ni ninguna otra entidad o servicio financiero externo**.

Por ejemplo, un usuario podrá crear cuentas como:

```text
Efectivo
Banco Nación
Mercado Pago
Tarjeta Visa
```

Estos nombres representan únicamente cuentas dentro del sistema. La plataforma no tendrá acceso a las cuentas reales del usuario, no consultará sus saldos reales ni podrá ejecutar operaciones sobre ellas.

Los saldos mostrados por la aplicación serán calculados exclusivamente a partir de los movimientos registrados por el propio usuario.

Por ejemplo:

```text
Cuenta: Banco Nación

Saldo inicial registrado:      $500.000
Ingreso registrado:           +$100.000
Gasto registrado:             -$ 40.000
                              ---------
Saldo en la aplicación:        $560.000
```

El saldo de `$560.000` representa el saldo calculado por la plataforma y no implica que el sistema haya consultado o verificado el saldo existente en la cuenta bancaria real.

### Transferencias internas

De la misma manera, una transferencia entre cuentas representa únicamente un **movimiento interno dentro del registro financiero de la aplicación**.

Por ejemplo:

> "Pasé $50.000 del Banco Nación a Mercado Pago."

El sistema podrá registrar:

```text
Banco Nación       -$50.000
Mercado Pago       +$50.000
```

pero **no realizará ninguna transferencia real de dinero** entre ambas cuentas.

La operación solamente modifica los registros y saldos internos de la plataforma.

Las transferencias deberán ejecutarse de forma atómica en el backend: el débito de una cuenta y el crédito de la otra deberán registrarse como una única operación lógica, de manera que ambos movimientos se completen correctamente o ninguno sea persistido.

Por lo tanto, el producto funciona como una herramienta de **registro, organización y consulta de información financiera personal**, y no como una plataforma bancaria, billetera virtual ni medio de pago.


## Stack tecnológico

El stack tecnológico se define buscando mantener una arquitectura simple para el MVP, incorporando únicamente componentes que tengan una responsabilidad concreta dentro del sistema.

| Capa | Tecnología | Responsabilidad dentro del proyecto |
|---|---|---|
| Orquestación del agente | OpenClaw | Gestiona el agente conversacional, su interacción con el LLM, el contexto de conversación y la invocación de tools que se comunican con el backend. |
| Backend | Python + FastAPI | Implementa la API, validaciones, autenticación/autorización, reglas de negocio y operaciones financieras del sistema. |
| Validación de datos | Pydantic | Define y valida los esquemas de entrada y salida utilizados por FastAPI. |
| Persistencia | PostgreSQL | Almacena usuarios, cuentas, movimientos, estado conversacional y auditoría, manteniendo integridad y consistencia transaccional. |
| ORM | SQLAlchemy | Gestiona el acceso del backend a PostgreSQL mediante modelos y operaciones de persistencia. |
| Migraciones | Alembic | Permite versionar y aplicar de forma controlada los cambios en el esquema de la base de datos. |
| Inteligencia artificial | API de LLM (proveedor a definir) | Interpreta lenguaje natural y permite al agente determinar la intención del usuario y los parámetros necesarios para utilizar las tools disponibles. |
| Frontend | React | Proporciona la interfaz web conversacional y las pantallas necesarias para la gestión y consulta de la información financiera. |
| Testing | pytest | Permite implementar pruebas unitarias y de integración sobre el backend y sus reglas de negocio. |
| Contenedores | Docker | Permite ejecutar los componentes del sistema en entornos reproducibles y simplificar su despliegue. |
| Despliegue | A definir | Al menos uno de los componentes principales será desplegado en un servicio online, de acuerdo con los requisitos del Trabajo Final. |

### Decisiones de simplificación para P0

Para el MVP se evitará incorporar infraestructura adicional que no sea necesaria para demostrar el funcionamiento del producto.

El estado conversacional se persistirá inicialmente en PostgreSQL, evitando incorporar Redis únicamente para esta función.

De la misma manera, P0 no requerirá:

- Redis;
- brokers o colas de mensajes;
- microservicios;
- múltiples canales de mensajería;
- sistemas complejos de procesamiento en segundo plano;
- integraciones con entidades financieras.

Las funcionalidades que posteriormente requieran tareas programadas, como los movimientos recurrentes de P1, comenzarán utilizando un mecanismo simple de scheduling. Solo se incorporará infraestructura adicional si aparece una necesidad técnica concreta que lo justifique.

### Separación de responsabilidades

La arquitectura mantendrá separadas las responsabilidades principales:

```text
React
  ↓
OpenClaw
  ↓
LLM / Agente
  ↓
Tools
  ↓
FastAPI
  ↓
Reglas de negocio
  ↓
PostgreSQL
```

OpenClaw y el LLM pertenecen a la capa conversacional y de interpretación.

FastAPI contiene la lógica de aplicación y las reglas financieras.

PostgreSQL constituye la fuente persistente de verdad del sistema.

Esta separación permite que los componentes de IA puedan modificarse o reemplazarse sin trasladar la lógica financiera fuera del backend.

## Experiencia previa del equipo

Antes de cerrar definitivamente el stack tecnológico se documentará el nivel de experiencia actual de los tres integrantes con las principales tecnologías involucradas en el proyecto.

| Tecnología | Aguilar | Alochis | Zupan |
|---|---|---|---|
| Python | Pendiente | Intermedio | Inicial |
| FastAPI | Pendiente | Inicial | Inicial |
| PostgreSQL | Pendiente | Inicial | Intermedio |
| React | Pendiente | Inicial | Intermedio |
| Docker | Pendiente | Inicial | Inicial |
| OpenClaw | Pendiente | Inicial | Inicial |
| Integración con LLM | Pendiente | Intermedio | Inicial |

Se utilizará como referencia la siguiente escala:

- **Inicial:** conocimientos introductorios o poca experiencia práctica.
- **Intermedio:** experiencia suficiente para desarrollar funcionalidades utilizando documentación y apoyo puntual.
- **Avanzado:** experiencia suficiente para trabajar de forma autónoma y resolver problemas habituales de la tecnología.

Esta evaluación permitirá verificar que el alcance y el stack elegidos sean compatibles con los conocimientos del equipo y que el proyecto no dependa del aprendizaje simultáneo de demasiadas tecnologías nuevas.

---

## Proveedor de LLM

**Estado: decisión pendiente.**

Antes de implementar la integración definitiva se seleccionará el proveedor y modelo de lenguaje que utilizará OpenClaw.

La elección tendrá en cuenta:

- compatibilidad con OpenClaw;
- soporte para tool/function calling y salidas estructuradas;
- costo por uso;
- límites de solicitudes;
- latencia;
- disponibilidad del servicio;
- manejo de timeouts y errores;
- privacidad de la información enviada;
- facilidad para reemplazar el proveedor si fuera necesario.

La lógica financiera no dependerá directamente del proveedor seleccionado. El modelo de lenguaje será utilizado para interpretar las solicitudes del usuario y seleccionar las tools correspondientes, mientras que las validaciones y operaciones financieras permanecerán en el backend.

---

## Seguridad y privacidad

El sistema manejará información personal y financiera registrada por los usuarios, por lo que se establecen los siguientes criterios iniciales de seguridad y privacidad.

### Autenticación y autorización

Todas las operaciones, tanto de lectura como de escritura, requerirán un usuario autenticado.

Las contraseñas serán almacenadas utilizando mecanismos seguros de hashing y nunca en texto plano.

Las credenciales, tokens y API keys de servicios externos no serán incluidas en el repositorio y se gestionarán mediante variables de entorno.

### Separación de datos entre usuarios

Las cuentas, movimientos y demás recursos financieros estarán asociados al usuario autenticado.

El identificador utilizado para determinar a qué usuario pertenece una operación será obtenido del contexto de autenticación del backend y no de información proporcionada por el LLM.

El backend verificará la pertenencia de cada recurso antes de permitir su consulta o modificación.

### Información enviada al LLM

Se aplicará un criterio de minimización de datos: únicamente se enviará al proveedor del modelo la información necesaria para interpretar la solicitud actual.

No se enviarán contraseñas, tokens, API keys ni credenciales del usuario.

Cuando una operación requiera contexto adicional, se enviará solamente la información estrictamente necesaria para resolver la interacción.

### Mensajes originales

Durante el desarrollo del proyecto los mensajes originales podrán conservarse como parte de la auditoría y del proceso de evaluación del sistema.

La política definitiva de conservación deberá considerar la utilidad de esta información para auditoría y pruebas frente a los requisitos de privacidad.

### Logs

Los logs técnicos no deberán almacenar:

- contraseñas;
- tokens de autenticación;
- API keys;
- credenciales;
- información sensible que no resulte necesaria para diagnosticar el funcionamiento del sistema.

La información necesaria para auditoría se almacenará de forma separada del logging técnico general.

### Fallas del servicio de IA

Ante un timeout, una respuesta inválida o la indisponibilidad del proveedor de IA:

- la operación solicitada no será ejecutada;
- no se realizará ninguna modificación sobre los datos financieros;
- el usuario recibirá una respuesta de error controlada;
- el sistema mantendrá la consistencia de la información existente.

---

## Auditoría

El sistema mantendrá un registro básico de las interacciones relevantes con el objetivo de proporcionar trazabilidad sobre las decisiones tomadas durante el procesamiento de una solicitud.

Para cada interacción podrán registrarse:

- usuario;
- fecha y hora;
- mensaje original;
- interpretación generada por el agente;
- tool seleccionada;
- parámetros interpretados;
- información faltante detectada;
- confirmaciones solicitadas;
- operación finalmente ejecutada;
- resultado de la operación.

Por ejemplo:

```text
Mensaje:
"Gasté 12.500 en una pizza"

Interpretación:
GASTO / $12.500 / alimentación

Dato faltante:
cuenta

Sistema:
"¿Desde qué cuenta lo pagaste?"

Usuario:
"Mercado Pago"

Operación final:
Gasto $12.500
Cuenta: Mercado Pago
Categoría: Alimentación

Resultado:
CONFIRMADO
```

Esta información permitirá demostrar durante la defensa el recorrido completo desde la interpretación realizada por el agente hasta la decisión final tomada por el backend.

---

## Estrategia de pruebas

La interpretación de lenguaje natural no será evaluada únicamente mediante ejemplos preparados para la demostración.

Se construirá progresivamente un conjunto de aproximadamente **50 a 100 expresiones representativas**, incluyendo casos simples, ambiguos, incompletos y expresados de diferentes maneras.

Por ejemplo:

```text
"Gasté 5000 en nafta"
"Pagué 20 lucas de luz"
"Ayer cobré 350 mil"
"Compré una pizza"
"Gasté 12.500 con Juan"
"El martes pagué Internet"
"Borrá el último gasto"
"Me gasté unos pesos en comida"
"Pagamos 30 entre tres"
```

Para cada expresión se evaluará:

- identificación correcta de la intención;
- extracción del monto;
- interpretación de la fecha;
- identificación o sugerencia de categoría;
- identificación de la cuenta cuando corresponda;
- detección de información faltante;
- detección de ambigüedades;
- solicitud de confirmación cuando corresponda;
- rechazo de operaciones que no puedan ejecutarse de manera segura.

Además de las pruebas sobre interpretación del lenguaje natural, se realizarán pruebas unitarias y de integración sobre las reglas determinísticas del backend y los principales flujos del sistema.

---

## Prueba técnica mínima

Antes de incorporar funcionalidades adicionales se implementará una prueba técnica end-to-end que permita validar la arquitectura principal del proyecto.

El circuito mínimo será:

```text
mensaje
   ↓
OpenClaw + LLM
   ↓
tool / solicitud estructurada
   ↓
FastAPI
   ↓
validación + reglas de negocio
   ↓
PostgreSQL
   ↓
respuesta
```

Por ejemplo, ante:

> "Gasté ayer $18.500 en supermercado con la Visa."

el sistema deberá interpretar la solicitud y el backend deberá comprobar:

1. que el usuario esté autenticado;
2. que la cuenta `Visa` exista;
3. que la cuenta pertenezca al usuario;
4. que el monto sea válido;
5. que la categoría sea válida;
6. que se encuentren presentes todos los datos necesarios;
7. que la operación pueda ejecutarse según las reglas del sistema.

Recién después de superar estas validaciones el movimiento podrá ser persistido.

Posteriormente, el usuario deberá poder consultar:

> "¿Cuánto gasté este mes en supermercado?"

y obtener una respuesta basada exclusivamente en los movimientos almacenados y calculados por el backend.

Completar correctamente este circuito será el primer hito técnico del proyecto antes de avanzar con funcionalidades P1 y P2.

---

## Estado del proyecto

Proyecto Final de la Tecnicatura en Programación, orientación Desarrollo Web.

Actualmente el proyecto se encuentra en etapa de definición funcional y técnica.

### Próximos pasos

1. Validar el problema con potenciales usuarios.
2. Completar la matriz de experiencia tecnológica del equipo.
3. Seleccionar el proveedor y modelo LLM.
4. Cerrar definitivamente el stack tecnológico de P0.
5. Definir los contratos de las tools y comandos estructurados.
6. Diseñar el modelo inicial de base de datos.
7. Implementar la prueba técnica mínima end-to-end.
8. Evaluar los resultados antes de incorporar funcionalidades P1 y P2.

---

## Licencia

A definir.
