# Frontend

Interfaz web de la Plataforma Conversacional de Finanzas Personales, desarrollada con React y Vite.

## Pantallas

- Inicio de sesion y registro de usuarios.
- Cuentas: listado con saldo actual, saldo total y alta de cuentas.
- Movimientos: registro de gastos e ingresos mediante formulario e historial con filtros.
- Resumen: gastos por categoria en un periodo.

Todas las pantallas incluyen la opcion de cambiar entre el tema claro y el tema de alto contraste.

## Requisitos

- Node.js 20 o superior.
- Backend en ejecucion (ver `backend/`).

## Instalacion y ejecucion

```bash
cd frontend
npm install
npm run dev
```

La aplicacion queda disponible en `http://localhost:5173`.

## Comunicacion con el backend

En desarrollo, Vite reenvia los pedidos que comienzan con `/api` al backend en `http://127.0.0.1:8000` (configurado en `vite.config.js`). De esta forma no es necesario habilitar CORS en el backend para trabajar localmente.

En produccion la direccion del backend se define mediante la variable de entorno `VITE_API_URL` (ver `.env.example`).

## Estructura

```text
src/
├── api/          comunicacion con el backend
├── components/   componentes compartidos (menu, rutas protegidas, tema)
├── context/      estado de la sesion
├── pages/        pantallas de la aplicacion
└── utils/        formato de importes y fechas, manejo del tema
```
