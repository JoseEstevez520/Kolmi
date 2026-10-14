import { ref, watch } from 'vue'
import { api } from './api.js'
import { supabase } from './supabase.js'

export const session = ref(null)
export const profile = ref(null)
export const ready = ref(false)

// The shell can be drawn before the server has answered. The last confirmed profile is kept per
// person and, when Supabase's own stored session is for that same person, both are used at
// once: `hinted` is true from then until the session has been read and the profile asked for
// again. It is for what is drawn and where a visit goes, nothing more: the server still decides
// on every request, and a disagreement is acted on as soon as it is known.
const SNAPSHOT = 'kolmi.profile.'

// Supabase keeps the session in localStorage; reading it there is synchronous.
function storedSession() {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (!/^sb-.+-auth-token$/.test(key)) continue
      const saved = JSON.parse(localStorage.getItem(key))
      if (saved?.access_token && saved?.user?.id) return saved
    }
  } catch {
    // Storage blocked or not JSON: no head start.
  }
  return null
}

function readSnapshot(id) {
  try {
    const saved = JSON.parse(localStorage.getItem(SNAPSHOT + id))
    return saved && typeof saved === 'object' && saved.role ? saved : null
  } catch {
    return null
  }
}

// Keeps `value` as `id`'s snapshot and drops everyone else's; with no value, drops them all.
function keepSnapshot(id, value) {
  try {
    Object.keys(localStorage)
      .filter((key) => key.startsWith(SNAPSHOT) && !(value && key === SNAPSHOT + id))
      .forEach((key) => localStorage.removeItem(key))
    if (id && value) localStorage.setItem(SNAPSHOT + id, JSON.stringify(value))
  } catch {
    // ignore
  }
}

const restored = storedSession()
const snapshot = restored ? readSnapshot(restored.user.id) : null
export const hinted = ref(Boolean(snapshot))
if (snapshot) {
  session.value = restored
  profile.value = snapshot
}

let resolveReady
// Resolves once the initial Supabase session has been read, so the router can
// wait before deciding where a visit goes.
export const authReady = new Promise((resolve) => {
  resolveReady = resolve
})

function markReady() {
  if (!ready.value) {
    ready.value = true
    resolveReady()
  }
}

// Another person's profile is never kept for a new session.
function setSession(next) {
  if (next?.user?.id !== session.value?.user?.id) profile.value = null
  session.value = next
}

supabase.auth.getSession().then(({ data }) => {
  setSession(data.session)
  markReady()
})

supabase.auth.onAuthStateChange((_event, next) => {
  setSession(next)
})

// The snapshot follows the profile; sign-out (or another person) clears it.
watch(
  [profile, () => (ready.value || hinted.value ? (session.value?.user?.id ?? null) : undefined)],
  ([current, id]) => {
    if (id !== undefined) keepSnapshot(id, id && current ? current : null)
  },
  { immediate: true },
)

// Whether the signed-in person has been let in. A profile with no status (an older backend)
// counts as active, so only a clear "pending" or "blocked" keeps someone out.
export function isWaiting(current) {
  return Boolean(current?.status) && current.status !== 'active'
}

export function accessToken() {
  return session.value?.access_token ?? null
}

// The name to prefill Register with, from the Google account when there is one.
export function displayName() {
  const user = session.value?.user
  return user?.user_metadata?.full_name || user?.user_metadata?.name || ''
}

export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw error
  setSession(data.session)
  return data.session
}

export async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({ email, password })
  if (error) throw error
  // With email confirmation off, signUp already returns a session.
  if (data.session) setSession(data.session)
  return data.session
}

export async function signInWithGoogle() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: `${window.location.origin}/` },
  })
  if (error) throw error
}

export async function resetPassword(email) {
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/login`,
  })
  if (error) throw error
}

export async function signOut() {
  await supabase.auth.signOut()
  setSession(null)
  profile.value = null
}

// Loads the caller's profile once and caches it. A 404 means there is no
// profile yet; anything else is a real error the caller should see.
export async function loadProfile(force = false) {
  if (profile.value && !force) return profile.value
  if (!session.value) {
    profile.value = null
    return null
  }
  try {
    profile.value = await api.getProfile()
  } catch (error) {
    if (error.status === 404) profile.value = null
    else throw error
  }
  return profile.value
}

// After a reload with a head start: once the session is read the profile is asked for again,
// whatever the snapshot said. If the server cannot be reached the snapshot stays as the shell it
// drew; anything else the server says wins at once.
export const confirmed = (async () => {
  await authReady
  if (!hinted.value) return
  try {
    if (session.value) await loadProfile(true)
  } catch (error) {
    if (error.status && error.status < 500) profile.value = null
  } finally {
    hinted.value = false
  }
})()
