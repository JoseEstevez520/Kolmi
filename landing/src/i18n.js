import { computed, reactive, ref } from 'vue'
import { defaultLabels } from 'elastic-ui'
import en from './locales/en.js'
import es from './locales/es.js'
import esLibrary from '../../frontend/src/locales/elastic-ui.es.js'

// The landing's two languages, each by its own name (what the switch shows). The texts are
// plain objects rather than vue-i18n messages: they carry code and commands, whose `@` and `{`
// would read as message syntax.
export const LOCALES = { en: 'English', es: 'Español' }

const MESSAGES = { en, es }
const LIBRARY_LABELS = { en: defaultLabels, es: esLibrary }
// The app's key, so a visitor who picked a language in the app keeps it here.
const STORAGE_KEY = 'kolmi.locale'

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
  const lang = navigator.languages?.[0] || navigator.language || ''
  return lang.toLowerCase().startsWith('es') ? 'es' : 'en'
}

export const locale = ref(savedLocale() || browserLocale())

/** The current language's texts. */
export const copy = computed(() => MESSAGES[locale.value])

// The labels elastic-ui is installed with, reactive so its parts follow a switch in place.
export const libraryLabels = reactive({ ...LIBRARY_LABELS[locale.value] })

function applyToDocument() {
  document.documentElement.lang = locale.value
  document.title = copy.value.meta.title
  document.querySelector('meta[name="description"]')?.setAttribute('content', copy.value.meta.description)
}

applyToDocument()

export function setLocale(next) {
  if (!(next in LOCALES) || next === locale.value) return
  Object.assign(libraryLabels, LIBRARY_LABELS[next])
  locale.value = next
  applyToDocument()
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // Private mode or blocked storage: the choice lasts until the tab closes.
  }
}
