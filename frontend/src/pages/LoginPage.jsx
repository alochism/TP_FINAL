
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { ThemeToggle } from '../components/ThemeToggle'
import { PasswordInput } from '../components/PasswordInput'
import { useAuth } from '../context/authContext'

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Si ya hay sesion iniciada no tiene sentido mostrar el login
  if (isAuthenticated) {
    return <Navigate to="/cuentas" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      navigate('/chat')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-theme">
        <ThemeToggle />
      </div>

      <form className="card auth-card" onSubmit={handleSubmit}>
        <h1>Iniciar sesión</h1>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Contraseña
          <PasswordInput
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? 'Ingresando...' : 'Ingresar'}
        </button>

        <p className="auth-link">
          ¿No tenés cuenta? <Link to="/registro">Registrate</Link>
        </p>
      </form>
    </div>
  )
}
