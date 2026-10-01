<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Callout, Field, Input } from 'elastic-ui'
import AuthLayout from '../components/AuthLayout.vue'
import GoogleIcon from '../components/GoogleIcon.vue'
import { resetPassword, signIn, signInWithGoogle } from '../lib/auth.js'

const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const info = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  info.value = ''
  loading.value = true
  try {
    await signIn(email.value.trim(), password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Could not sign in.'
  } finally {
    loading.value = false
  }
}

async function withGoogle() {
  error.value = ''
  info.value = ''
  try {
    await signInWithGoogle()
  } catch (e) {
    error.value = e.message || 'Could not start Google sign-in.'
  }
}

async function forgot() {
  error.value = ''
  info.value = ''
  const address = email.value.trim()
  if (!address) {
    error.value = 'Write your email first, then tap "Forgot my password".'
    return
  }
  try {
    await resetPassword(address)
    info.value = `If ${address} has an account, we sent it a link to set a new password.`
  } catch (e) {
    error.value = e.message || 'Could not send the reset email.'
  }
}
</script>

<template>
  <AuthLayout>
    <div class="flex flex-col gap-6">
      <Button variant="outline" :icon="GoogleIcon" @click="withGoogle">
        Sign in with Google
      </Button>

      <div class="flex items-center gap-3 text-xs text-fg-muted">
        <span class="h-px flex-1 bg-border" />
        or
        <span class="h-px flex-1 bg-border" />
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <Field label="Email">
          <Input v-model="email" type="email" autocomplete="email" required />
        </Field>
        <Field label="Password">
          <Input v-model="password" type="password" autocomplete="current-password" required />
        </Field>

        <Callout v-if="error" type="caution" title="Could not sign in">{{ error }}</Callout>
        <Callout v-else-if="info" type="note" title="Check your email">{{ info }}</Callout>

        <Button type="submit" :loading="loading">Sign in</Button>
      </form>

      <div class="flex flex-wrap justify-center gap-x-4 gap-y-2 text-sm">
        <RouterLink class="text-fg-secondary hover:text-fg" to="/register">Sign up</RouterLink>
        <button
          class="cursor-pointer text-fg-secondary hover:text-fg"
          type="button"
          @click="forgot"
        >
          Forgot my password
        </button>
      </div>
    </div>
  </AuthLayout>
</template>
