import { useState } from 'react'
import { applyTheme, getSavedTheme, THEMES } from '../utils/theme'

// Alterna entre el tema claro y el de alto contraste.
// El alto contraste mejora la lectura con mucha luz o en pantallas con poco brillo
export function ThemeToggle() {
  const [theme, setTheme] = useState(getSavedTheme())

  function handleClick() {
    const newTheme = theme === THEMES.light ? THEMES.contrast : THEMES.light

    applyTheme(newTheme)
    setTheme(newTheme)
  }

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={handleClick}
      aria-pressed={theme === THEMES.contrast}
    >
      {theme === THEMES.light ? 'Alto contraste' : 'Tema claro'}
    </button>
  )
}
