// URL base del backend.
// En desarrollo se usa /api y el proxy de Vite lo reenvia al backend.
// En produccion se define VITE_API_URL con la direccion del backend desplegado
const API_URL = import.meta.env.VITE_API_URL || '/api'

const TOKEN_KEY = 'token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// Error propio para conservar el codigo HTTP devuelto por el backend
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

// Convierte la respuesta de error de FastAPI en un mensaje legible.
// detail puede ser un texto (errores de negocio) o una lista (errores de validacion)
function getErrorMessage(data) {
  if (!data || !data.detail) {
    return 'Ocurrio un error inesperado'
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  return 'Revisa los datos ingresados'
}

// Funcion unica para comunicarse con el backend.
// Agrega el token cuando existe, de modo que cada pantalla no tenga que hacerlo
export async function apiRequest(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response

  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method || 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiError('No se pudo conectar con el servidor', 0)
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    // Token vencido o invalido: se cierra la sesion y se vuelve al login
    if (response.status === 401 && token) {
      removeToken()
      window.location.href = '/login'
    }

    throw new ApiError(getErrorMessage(data), response.status)
  }

  return data
}
