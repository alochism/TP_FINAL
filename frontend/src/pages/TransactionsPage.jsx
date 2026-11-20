import { useEffect, useState } from 'react'
import { apiRequest } from '../api/client'
import {
  formatCurrency,
  formatDate,
  todayIso,
  TRANSACTION_TYPES,
} from '../utils/format'

const EMPTY_FILTERS = {
  type: '',
  accountId: '',
  categoryId: '',
  dateFrom: '',
  dateTo: '',
}

function emptyForm() {
  return {
    type: 'EXPENSE',
    accountId: '',
    categoryId: '',
    amount: '',
    date: todayIso(),
    description: '',
  }
}

// Arma la consulta con los filtros completados.
// Los filtros vacios no se envian para que el backend no los aplique
function buildQuery(filters) {
  const params = new URLSearchParams()

  if (filters.type) params.append('type', filters.type)
  if (filters.accountId) params.append('account_id', filters.accountId)
  if (filters.categoryId) params.append('category_id', filters.categoryId)
  if (filters.dateFrom) params.append('date_from', filters.dateFrom)
  if (filters.dateTo) params.append('date_to', filters.dateTo)

  const query = params.toString()
  return query ? `?${query}` : ''
}

export function TransactionsPage() {
  const [accounts, setAccounts] = useState([])
  const [categories, setCategories] = useState([])
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [filters, setFilters] = useState(EMPTY_FILTERS)

  const [form, setForm] = useState(emptyForm())
  const [formError, setFormError] = useState('')
  const [formSuccess, setFormSuccess] = useState('')
  const [saving, setSaving] = useState(false)

  // Cuentas y categorias se cargan una sola vez: se usan en el formulario,
  // en los filtros y para mostrar nombres en lugar de identificadores
  useEffect(() => {
    Promise.all([apiRequest('/accounts'), apiRequest('/categories')])
      .then(([accountsData, categoriesData]) => {
        setAccounts(accountsData)
        setCategories(categoriesData)
      })
      .catch((err) => setError(err.message))
  }, [])

  // El historial se vuelve a pedir cada vez que cambia algun filtro
  useEffect(() => {
    apiRequest(`/transactions${buildQuery(filters)}`)
      .then(setTransactions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [filters])

  // Anulacion logica: el movimiento se conserva y deja de contar en los saldos.
  // Al ser una operacion destructiva se pide confirmacion siempre
  async function handleVoid(transaction) {
    const confirmed = window.confirm(
      `¿Anular el movimiento de ${formatCurrency(transaction.amount)} del ${formatDate(transaction.date)}? ` +
        'Dejará de contar en los saldos.'
    )

    if (!confirmed) return

    try {
      const updated = await apiRequest(`/transactions/${transaction.id}/void`, { method: 'PATCH' })
      setTransactions((current) => current.map((item) => (item.id === updated.id ? updated : item)))
    } catch (err) {
      setError(err.message)
    }
  }

  function getAccountName(accountId) {
    const account = accounts.find((item) => item.id === accountId)
    return account ? account.name : '-'
  }

  function getCategoryName(categoryId) {
    const category = categories.find((item) => item.id === categoryId)
    return category ? category.name : '-'
  }

  // En el formulario solo se ofrecen las categorias del tipo elegido
  const formCategories = categories.filter((category) => category.type === form.type)

  function handleFormChange(event) {
    const { name, value } = event.target

    // Al cambiar entre gasto e ingreso la categoria elegida deja de ser valida
    if (name === 'type') {
      setForm({ ...form, type: value, categoryId: '' })
      return
    }

    setForm({ ...form, [name]: value })
  }

  function handleFilterChange(event) {
    setFilters({ ...filters, [event.target.name]: event.target.value })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setFormSuccess('')
    setSaving(true)

    // Gastos e ingresos se registran en endpoints distintos del backend
    const path = form.type === 'EXPENSE' ? '/transactions/expense' : '/transactions/income'

    try {
      await apiRequest(path, {
        method: 'POST',
        body: {
          account_id: Number(form.accountId),
          category_id: Number(form.categoryId),
          amount: form.amount,
          date: form.date,
          description: form.description || null,
        },
      })

      setFormSuccess(`${TRANSACTION_TYPES[form.type]} registrado correctamente`)
      setForm({ ...emptyForm(), type: form.type, accountId: form.accountId })

      // Se copian los filtros para forzar la recarga del historial
      setFilters({ ...filters })
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <h1>Movimientos</h1>

      {accounts.length === 0 && !loading && (
        <p>Para registrar movimientos primero tenés que crear una cuenta.</p>
      )}

      <form className="card form" onSubmit={handleSubmit}>
        <h2>Nuevo movimiento</h2>

        <div className="type-selector" role="radiogroup" aria-label="Tipo de movimiento">
          {Object.entries(TRANSACTION_TYPES).map(([value, label]) => (
            <label key={value} className={form.type === value ? 'selected' : ''}>
              <input
                type="radio"
                name="type"
                value={value}
                checked={form.type === value}
                onChange={handleFormChange}
              />
              {label}
            </label>
          ))}
        </div>

        <label>
          Cuenta
          <select name="accountId" value={form.accountId} onChange={handleFormChange} required>
            <option value="">Elegí una cuenta</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Categoría
          <select name="categoryId" value={form.categoryId} onChange={handleFormChange} required>
            <option value="">Elegí una categoría</option>
            {formCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Monto (ARS)
          <input
            name="amount"
            type="number"
            min="0.01"
            step="0.01"
            value={form.amount}
            onChange={handleFormChange}
            required
          />
        </label>

        <label>
          Fecha
          <input name="date" type="date" value={form.date} onChange={handleFormChange} required />
        </label>

        <label>
          Descripción (opcional)
          <input
            name="description"
            value={form.description}
            onChange={handleFormChange}
            maxLength="255"
            placeholder="Ej: compra en el supermercado"
          />
        </label>

        {formError && <p className="error">{formError}</p>}
        {formSuccess && <p className="success">{formSuccess}</p>}

        <button type="submit" disabled={saving}>
          {saving ? 'Guardando...' : 'Registrar'}
        </button>
      </form>

      <h2 className="section-title">Historial</h2>

      <div className="filters">
        <label>
          Tipo
          <select name="type" value={filters.type} onChange={handleFilterChange}>
            <option value="">Todos</option>
            {Object.entries(TRANSACTION_TYPES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Cuenta
          <select name="accountId" value={filters.accountId} onChange={handleFilterChange}>
            <option value="">Todas</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Categoría
          <select name="categoryId" value={filters.categoryId} onChange={handleFilterChange}>
            <option value="">Todas</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name} ({TRANSACTION_TYPES[category.type]})
              </option>
            ))}
          </select>
        </label>

        <label>
          Desde
          <input name="dateFrom" type="date" value={filters.dateFrom} onChange={handleFilterChange} />
        </label>

        <label>
          Hasta
          <input name="dateTo" type="date" value={filters.dateTo} onChange={handleFilterChange} />
        </label>

        <button type="button" className="button-secondary" onClick={() => setFilters(EMPTY_FILTERS)}>
          Limpiar filtros
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p>Cargando movimientos...</p>}

      {!loading && transactions.length === 0 && <p>No hay movimientos para mostrar.</p>}

      {transactions.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Tipo</th>
              <th>Categoría</th>
              <th>Cuenta</th>
              <th>Descripción</th>
              <th className="amount">Monto</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.id} className={transaction.status === 'VOIDED' ? 'voided' : ''}>
                <td>{formatDate(transaction.date)}</td>
                <td>{TRANSACTION_TYPES[transaction.type]}</td>
                <td>{getCategoryName(transaction.category_id)}</td>
                <td>{getAccountName(transaction.account_id)}</td>
                <td>{transaction.description || '-'}</td>
                <td className={`amount ${transaction.type === 'INCOME' ? 'income' : 'expense'}`}>
                  {transaction.type === 'INCOME' ? '+ ' : '- '}
                  {formatCurrency(transaction.amount)}
                </td>
                <td>
                  {transaction.status === 'VOIDED' ? (
                    'Anulado'
                  ) : (
                    <button type="button" className="button-secondary button-small" onClick={() => handleVoid(transaction)}>
                      Anular
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
