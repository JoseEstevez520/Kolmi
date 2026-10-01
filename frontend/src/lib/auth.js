import { ref } from 'vue'
import { api } from './api.js'
import { supabase } from './supabase.js'

export const session = ref(null)
export const profile = ref(null)
export const ready = ref(false)

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

supabase.auth.getSession().then(({ data }) => {
  session.value = data.session
  markReady()
})

supabase.auth.onAuthStateChange((_event, next) => {
  session.value = next
  if (!next) profile.value = null
})

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
  session.value = data.session
  return data.session
}

export async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({ email, password })
  if (error) throw error
  // With email confirmation off, signUp already returns a session.
  if (data.session) session.value = data.session
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
  session.value = null
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
