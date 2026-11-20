import { NavLink, Outlet, useNavigate } from 'react-router'
import { useAuth } from '../context/authContext'
import { ThemeToggle } from './ThemeToggle'

// Estructura comun de las pantallas internas: encabezado con menu y contenido
export function Layout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <header className="header">
        <span className="brand">Finanzas Personales</span>

        <nav className="nav">
          <NavLink to="/cuentas">Cuentas</NavLink>
          <NavLink to="/movimientos">Movimientos</NavLink>
          <NavLink to="/resumen">Resumen</NavLink>
        </nav>

        <div className="header-actions">
          <ThemeToggle />
          <button type="button" className="button-secondary" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
