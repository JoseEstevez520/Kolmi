import { currentLocale } from './i18n.js'

// A short line saying where a bug report came from: browser, system, screen width, theme and
// language. Nothing that identifies the person. The app has no build version to add.
const BROWSERS = [
  ['Edg', 'Edge'],
  ['OPR', 'Opera'],
  ['Firefox', 'Firefox'],
  ['Chrome', 'Chrome'],
  ['Version', 'Safari'],
]

function browser(ua) {
  for (const [token, name] of BROWSERS) {
    const found = ua.match(new RegExp(`${token}/(\\d+)`))
    if (found) return `${name} ${found[1]}`
  }
  return 'Unknown browser'
}

function system(ua) {
  if (/Android/.test(ua)) return 'Android'
  if (/iPhone|iPad|iPod/.test(ua)) return 'iOS'
  if (/Windows/.test(ua)) return 'Windows'
  if (/Mac OS X/.test(ua)) return 'macOS'
  if (/CrOS/.test(ua)) return 'ChromeOS'
  if (/Linux/.test(ua)) return 'Linux'
  return null
}

// elastic-ui's theme lives as `data-theme` on <html>; before the person picks one it follows the system.
function theme() {
  const set = document.documentElement.dataset.theme
  if (set === 'dark' || set === 'light') return set
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function describeEnvironment() {
  const ua = navigator.userAgent || ''
  const os = system(ua)
  return [
    `${browser(ua)}${os ? ` on ${os}` : ''}`,
    `${window.innerWidth}px`,
    `${theme()} theme`,
    currentLocale(),
  ].join(', ')
}
