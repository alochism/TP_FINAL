import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import App from './App.jsx'
import { AuthProvider } from './context/AuthProvider'
import './index.css'
import { applyTheme, getSavedTheme } from './utils/theme'

// Se aplica el tema guardado antes de mostrar la aplicacion para evitar un cambio visible de colores
applyTheme(getSavedTheme())

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
