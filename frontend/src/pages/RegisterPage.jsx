
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { ThemeToggle } from '../components/ThemeToggle'
import { PasswordInput } from '../components/PasswordInput'
import { useAuth } from '../context/authContext'

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [confirmEmail, setConfirmEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const emailsMatch =
    email.trim() !== '' &&
    confirmEmail.trim() !== '' &&
    email.trim().toLowerCase() === confirmEmail.trim().toLowerCase()

  const passwordsMatch =
    password !== '' &&
    password === confirmPassword

  const passwordValid =
    password.length >= 8 &&
    new TextEncoder().encode(password).length <= 72

  const canSubmit =
    emailsMatch &&
    passwordsMatch &&
    passwordValid &&
    !loading

  if (isAuthenticated) {
    return <Navigate to="/cuentas" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (!canSubmit) return

    setError('')
    setLoading(true)

    try {
      await register(email.trim(), password)
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
        <h1>Crear cuenta</h1>

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
          Repetir email
          <input
            type="email"
            value={confirmEmail}
            onChange={(event) => setConfirmEmail(event.target.value)}
            autoComplete="off"
            required
          />
        </label>

        {confirmEmail && !emailsMatch && (
          <p className="error">Los emails no coinciden.</p>
        )}

        <label>
          Contraseña
          <PasswordInput
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>

        {password.length > 0 && password.length < 8 && (
          <p className="error">
            La contraseña debe tener al menos 8 caracteres.
          </p>
        )}

        {password.length > 0 &&
          new TextEncoder().encode(password).length > 72 && (
            <p className="error">
              La contraseña no puede superar los 72 bytes.
            </p>
          )}

        <label>
          Repetir contraseña
          <PasswordInput
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </label>

        {confirmPassword && !passwordsMatch && (
          <p className="error">Las contraseñas no coinciden.</p>
        )}

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={!canSubmit}>
          {loading ? 'Creando cuenta...' : 'Registrarme'}
        </button>

        <p className="auth-link">
          ¿Ya tenés cuenta? <Link to="/login">Iniciá sesión</Link>
        </p>
      </form>
    </div>
  )
}
