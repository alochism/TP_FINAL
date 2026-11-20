import { useEffect, useState } from 'react'
import { apiRequest } from '../api/client'
import { firstDayOfMonthIso, formatCurrency, todayIso } from '../utils/format'

// Por defecto se muestra el mes en curso
function defaultFilters() {
  return {
    dateFrom: firstDayOfMonthIso(),
    dateTo: todayIso(),
    accountId: '',
  }
}

function buildQuery(filters) {
  const params = new URLSearchParams()

  if (filters.dateFrom) params.append('date_from', filters.dateFrom)
  if (filters.dateTo) params.append('date_to', filters.dateTo)
  if (filters.accountId) params.append('account_id', filters.accountId)

  const query = params.toString()
  return query ? `?${query}` : ''
}

export function SummaryPage() {
  const [accounts, setAccounts] = useState([])
  const [expenses, setExpenses] = useState([])
  const [filters, setFilters] = useState(defaultFilters())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    apiRequest('/accounts')
      .then(setAccounts)
      .catch((err) => setError(err.message))
  }, [])

  // Los totales por categoria los calcula el backend con una consulta agrupada
  useEffect(() => {
    apiRequest(`/transactions/expenses-by-category${buildQuery(filters)}`)
      .then(setExpenses)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [filters])

  function handleFilterChange(event) {
    setFilters({ ...filters, [event.target.name]: event.target.value })
  }

  // El total y los porcentajes son solo para presentar la informacion
  const total = expenses.reduce((sum, item) => sum + Number(item.total), 0)

  function getPercentage(amount) {
    return total > 0 ? (Number(amount) / total) * 100 : 0
  }

  return (
    <section>
      <h1>Gastos por categoría</h1>

      <div className="filters">
        <label>
          Desde
          <input name="dateFrom" type="date" value={filters.dateFrom} onChange={handleFilterChange} />
        </label>

        <label>
          Hasta
          <input name="dateTo" type="date" value={filters.dateTo} onChange={handleFilterChange} />
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

        <button type="button" className="button-secondary" onClick={() => setFilters(defaultFilters())}>
          Mes actual
        </button>
      </div>

      <div className="card total">
        <span>Total gastado en el período</span>
        <strong>{formatCurrency(total)}</strong>
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p>Cargando resumen...</p>}

      {!loading && !error && expenses.length === 0 && (
        <p>No hay gastos registrados en el período seleccionado.</p>
      )}

      {expenses.length > 0 && (
        <ul className="card category-list">
          {expenses.map((item) => {
            const percentage = getPercentage(item.total)

            return (
              <li key={item.category}>
                <div className="category-row">
                  <span>{item.category}</span>
                  <span>
                    {formatCurrency(item.total)} <small>({percentage.toFixed(1)}%)</small>
                  </span>
                </div>

                {/* Barra proporcional al porcentaje del total, hecha solo con CSS */}
                <div className="bar" aria-hidden="true">
                  <div className="bar-fill" style={{ width: `${percentage}%` }} />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
