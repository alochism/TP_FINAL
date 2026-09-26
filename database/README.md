# Base de datos

La aplicacion utiliza PostgreSQL como sistema de gestion de base de datos relacional.

El diseño completo del modelo de datos se encuentra documentado en:

`docs/modelo-datos.md`

Alli se detallan:

- Entidades y atributos.
- Tipos de datos.
- Claves primarias y foraneas.
- Relaciones.
- Indices principales.
- Diagrama entidad-relacion.
- Decisiones de diseño.

## Versionado del esquema

Durante la implementacion, los cambios sobre el esquema de la base de datos se gestionan mediante Alembic.

Las migraciones se encuentran en:

`backend/alembic/`

De esta forma se mantiene una unica fuente para la implementacion y versionado del esquema, evitando duplicar scripts SQL que puedan quedar desactualizados respecto de las migraciones.

## Motor de base de datos

- PostgreSQL
- SQLAlchemy como ORM
- Alembic para migraciones y versionado del esquema