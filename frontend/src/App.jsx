import { Navigate, Route, Routes } from 'react-router'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AccountsPage } from './pages/AccountsPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { SummaryPage } from './pages/SummaryPage'
import { TransactionsPage } from './pages/TransactionsPage'

// Rutas de la aplicacion.
// Las pantallas internas quedan dentro de ProtectedRoute y comparten el Layout
function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/cuentas" element={<AccountsPage />} />
          <Route path="/movimientos" element={<TransactionsPage />} />
          <Route path="/resumen" element={<SummaryPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/cuentas" replace />} />
    </Routes>
  )
}

export default App
