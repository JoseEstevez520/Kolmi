import { createI18n } from 'vue-i18n'
import { defaultLabels } from 'elastic-ui'
import en from '../locales/en.js'
import es from '../locales/es.js'
import esLibrary from '../locales/elastic-ui.es.js'

// The app's languages, each by its own name (what the switch shows).
export const LOCALES = { en: 'English', es: 'Español' }

const STORAGE_KEY = 'kolmi.locale'
const LIBRARY_LABELS = { en: defaultLabels, es: esLibrary }

function savedLocale() {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value && value in LOCALES ? value : null
  } catch {
    return null
  }
}

// A Spanish browser (es, es-ES, es-MX…) gets Spanish; anything else, English.
function browserLocale() {
  const lang = (typeof navigator !== 'undefined' && (navigator.languages?.[0] || navigator.language)) || ''
  return lang.toLowerCase().startsWith('es') ? 'es' : 'en'
}

const initial = savedLocale() || browserLocale()

export const i18n = createI18n({
  legacy: false,
  locale: initial,
  fallbackLocale: 'en',
  messages: { en, es },
})

// The labels elastic-ui is installed with. The library reads them when a part is created, so
// switching the language updates this object and App.vue remounts the tree under its key.
export const libraryLabels = { ...LIBRARY_LABELS[initial] }

/** A message outside a component (lib code): the same `t` the templates use. */
export const t = (...args) => i18n.global.t(...args)

/** Whether a message exists, for labels looked up by a value from the backend. */
export const te = (key) => i18n.global.te(key, 'en')

/** The current language, for code that formats dates and numbers. */
export const currentLocale = () => i18n.global.locale.value

function applyToDocument(locale) {
  document.documentElement.lang = locale
  document.title = t('app.title')
}

applyToDocument(initial)

export function setLocale(locale) {
  if (!(locale in LOCALES) || locale === currentLocale()) return
  Object.assign(libraryLabels, LIBRARY_LABELS[locale])
  i18n.global.locale.value = locale
  applyToDocument(locale)
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // Private mode or blocked storage: the choice lasts until the tab closes.
  }
}
