// Formatea un importe en pesos argentinos (ej: $ 18.500,00).
// El backend devuelve los importes como texto para no perder precision decimal
const currencyFormat = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
})

export function formatCurrency(amount) {
  return currencyFormat.format(Number(amount))
}

export const ACCOUNT_TYPES = {
  CASH: 'Efectivo',
  BANK: 'Cuenta bancaria',
  WALLET: 'Billetera virtual',
}

export const TRANSACTION_TYPES = {
  EXPENSE: 'Gasto',
  INCOME: 'Ingreso',
}

// Muestra una fecha del backend (AAAA-MM-DD) como DD/MM/AAAA.
// Se arma a mano para evitar que la zona horaria corra la fecha un dia
export function formatDate(isoDate) {
  const [year, month, day] = isoDate.split('-')
  return `${day}/${month}/${year}`
}

// Fecha actual en formato AAAA-MM-DD, el que usan los campos de tipo date
export function todayIso() {
  const today = new Date()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${today.getFullYear()}-${month}-${day}`
}

// Primer dia del mes actual en formato AAAA-MM-DD
export function firstDayOfMonthIso() {
  return `${todayIso().slice(0, 8)}01`
}
