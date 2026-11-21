import { Navigate, Outlet } from 'react-router'
import { useAuth } from '../context/authContext'

// Solo deja pasar a las pantallas internas si hay una sesion iniciada.
// Es una comodidad de navegacion: la proteccion real la hace el backend con el token
export function ProtectedRoute() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
