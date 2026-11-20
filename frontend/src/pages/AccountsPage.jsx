import { useEffect, useState } from 'react'
import { apiRequest } from '../api/client'
import { ACCOUNT_TYPES, formatCurrency } from '../utils/format'

// Obtiene las cuentas del usuario junto con el saldo de cada una y el saldo total.
// Los saldos los calcula el backend a partir de los movimientos registrados
async function fetchAccountsData() {
  const accounts = await apiRequest('/accounts')

  const balances = await Promise.all(
    accounts.map((account) => apiRequest(`/accounts/balance?account_id=${account.id}`))
  )

  const total = await apiRequest('/accounts/balance')

  const accountsWithBalance = accounts.map((account, index) => ({
    ...account,
    balance: balances[index].balance,
  }))

  return { accounts: accountsWithBalance, total: total.balance }
}

const EMPTY_FORM = {
  name: '',
  type: 'CASH',
  initialBalance: '',
}

export function AccountsPage() {
  const [accounts, setAccounts] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  function showData(data) {
    setAccounts(data.accounts)
    setTotal(data.total)
  }

  useEffect(() => {
    fetchAccountsData()
      .then(showData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(event) {
    setForm({ ...form, [event.target.name]: event.target.value })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setSaving(true)

    try {
      // En P0 todas las cuentas son en pesos, por eso la moneda no se pide
      await apiRequest('/accounts', {
        method: 'POST',
        body: {
          name: form.name,
          type: form.type,
          initial_balance: form.initialBalance || 0,
        },
      })

      setForm(EMPTY_FORM)
      showData(await fetchAccountsData())
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSaving(false)
    }
  }

  // Desactivacion logica: la cuenta deja de aparecer y no se puede usar,
  // pero sus movimientos se conservan. Se pide confirmacion siempre
  async function handleDeactivate(account) {
    const confirmed = window.confirm(
      `¿Desactivar la cuenta "${account.name}"? No se podrá usar para registrar movimientos.`
    )

    if (!confirmed) return

    try {
      await apiRequest(`/accounts/${account.id}/deactivate`, { method: 'PATCH' })
      showData(await fetchAccountsData())
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section>
      <h1>Cuentas</h1>

      <div className="card total">
        <span>Saldo total</span>
        <strong>{formatCurrency(total)}</strong>
      </div>

      {loading && <p>Cargando cuentas...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && accounts.length === 0 && (
        <p>Todavía no registraste cuentas. Creá la primera con el formulario.</p>
      )}

      {accounts.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tipo</th>
              <th className="amount">Saldo inicial</th>
              <th className="amount">Saldo actual</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => (
              <tr key={account.id}>
                <td>{account.name}</td>
                <td>{ACCOUNT_TYPES[account.type]}</td>
                <td className="amount">{formatCurrency(account.initial_balance)}</td>
                <td className="amount">{formatCurrency(account.balance)}</td>
                <td>
                  <button type="button" className="button-secondary button-small" onClick={() => handleDeactivate(account)}>
                    Desactivar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form className="card form" onSubmit={handleSubmit}>
        <h2>Nueva cuenta</h2>

        <label>
          Nombre
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Ej: Banco Provincia del Neuquén"
            required
          />
        </label>

        <label>
          Tipo
          <select name="type" value={form.type} onChange={handleChange}>
            {Object.entries(ACCOUNT_TYPES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Saldo inicial (ARS)
          <input
            name="initialBalance"
            type="number"
            min="0"
            step="0.01"
            value={form.initialBalance}
            onChange={handleChange}
            placeholder="0,00"
          />
        </label>

        {formError && <p className="error">{formError}</p>}

        <button type="submit" disabled={saving}>
          {saving ? 'Guardando...' : 'Crear cuenta'}
        </button>
      </form>
    </section>
  )
}
