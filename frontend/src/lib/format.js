import { currentLocale, t, te } from './i18n.js'

// Formatters per language, built once each.
const formatters = new Map()

function formatter(kind, options) {
  const locale = currentLocale()
  const key = `${kind}:${locale}`
  if (!formatters.has(key)) formatters.set(key, new Intl.DateTimeFormat(locale, options))
  return formatters.get(key)
}

function toDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value) {
  const date = toDate(value)
  return date ? formatter('long', { dateStyle: 'medium', timeStyle: 'short' }).format(date) : ''
}

// Just the day, for when someone joined.
export function formatDay(value) {
  const date = toDate(value)
  return date ? formatter('day', { dateStyle: 'medium' }).format(date) : ''
}

// For narrow cells (the AI log): day, short month and the time, no year.
export function formatShortDate(value) {
  const date = toDate(value)
  if (!date) return ''
  return formatter('short', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(date)
}

// How long something took, in its largest unit: "45 s", "3 min", "2 h".
export function formatDuration(from, to) {
  const start = toDate(from)
  const end = toDate(to)
  if (!start || !end) return ''
  const seconds = Math.max(0, Math.round((end - start) / 1000))
  const [amount, unit] =
    seconds < 60
      ? [seconds, 'second']
      : seconds < 3600
        ? [Math.round(seconds / 60), 'minute']
        : [Math.round(seconds / 360) / 10, 'hour']
  return new Intl.NumberFormat(currentLocale(), { style: 'unit', unit, unitDisplay: 'short' }).format(
    amount,
  )
}

export function noteStatusLabel(status) {
  const key = `notes.status.${status}`
  return status && te(key) ? t(key) : status
}
