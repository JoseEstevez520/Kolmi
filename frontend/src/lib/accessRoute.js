// Only the consent route may survive a login; external redirect destinations never do.
export function consentDestination(value) {
  return typeof value === 'string' && value.startsWith('/oauth/consent?') ? value : null
}

export function decideRoute(to, current, signedIn) {
  if (!signedIn) return to.meta.public ? true : {
    name: 'login', query: to.name === 'oauth-consent' ? { redirect: to.fullPath } : {},
  }
  if (!current) return to.name === 'register' ? true : { name: 'register' }
  if (Boolean(current.status) && current.status !== 'active') {
    return to.name === 'waiting' || to.name === 'login' ? true : { name: 'waiting' }
  }
  if (to.name === 'login') return consentDestination(to.query?.redirect) || { name: 'home' }
  if (to.name === 'waiting' || to.name === 'register') return { name: 'home' }
  if (to.meta.admin && current.role !== 'admin') return { name: 'home' }
  return true
}
