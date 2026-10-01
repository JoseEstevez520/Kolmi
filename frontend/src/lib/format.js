const dateFormatter = new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' })

export function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : dateFormatter.format(date)
}

const STATUS_LABELS = {
  pending: 'Pending',
  processed: 'Processed',
  discarded: 'Discarded',
}

export function noteStatusLabel(status) {
  return STATUS_LABELS[status] ?? status
}
