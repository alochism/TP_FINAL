import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

// Permite que cualquier componente acceda a la sesion actual
export function useAuth() {
  return useContext(AuthContext)
}
