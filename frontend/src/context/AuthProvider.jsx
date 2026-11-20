import { useState } from 'react'
import { apiRequest, getToken, removeToken, saveToken } from '../api/client'
import { AuthContext } from './authContext'

// Mantiene el estado de la sesion para toda la aplicacion.
// El usuario se identifica solo por el token: el backend obtiene
// el usuario a partir de el y no de datos enviados por el front
export function AuthProvider({ children }) {
  const [token, setToken] = useState(getToken())

  async function login(email, password) {
    const data = await apiRequest('/auth/login', {
      method: 'POST',
      body: { email, password },
    })

    saveToken(data.access_token)
    setToken(data.access_token)
  }

  // Luego de registrarse se inicia sesion automaticamente
  async function register(email, password) {
    await apiRequest('/auth/register', {
      method: 'POST',
      body: { email, password },
    })

    await login(email, password)
  }

  function logout() {
    removeToken()
    setToken(null)
  }

  const value = {
    isAuthenticated: Boolean(token),
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
