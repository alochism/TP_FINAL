const THEME_KEY = 'theme'

export const THEMES = {
  light: 'light',
  contrast: 'contrast',
}

export function getSavedTheme() {
  return localStorage.getItem(THEME_KEY) || THEMES.light
}

// El tema se aplica como atributo del html y el CSS cambia los colores segun su valor
export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme
  localStorage.setItem(THEME_KEY, theme)
}
