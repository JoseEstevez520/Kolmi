<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Field, Input } from 'elastic-ui'
import AuthLayout from '../components/AuthLayout.vue'
import GoogleIcon from '../components/GoogleIcon.vue'
import { resetPassword, signIn, signInWithGoogle } from '../lib/auth.js'

const router = useRouter()
const { t } = useI18n()

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
    error.value = e.message || t('login.errorLong')
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
    error.value = e.message || t('login.googleError')
  }
}

async function forgot() {
  error.value = ''
  info.value = ''
  const address = email.value.trim()
  if (!address) {
    error.value = t('login.emailFirst', { action: t('login.forgot') })
    return
  }
  try {
    await resetPassword(address)
    info.value = t('login.resetSent', { email: address })
  } catch (e) {
    error.value = e.message || t('login.resetError')
  }
}
</script>

<template>
  <AuthLayout>
    <div class="flex flex-col gap-6">
      <Button variant="outline" :icon="GoogleIcon" @click="withGoogle">
        {{ t('login.google') }}
      </Button>

      <div class="flex items-center gap-3 text-xs text-fg-muted">
        <span class="h-px flex-1 bg-border" />
        {{ t('login.or') }}
        <span class="h-px flex-1 bg-border" />
      </div>

      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <Field :label="t('login.email')">
          <Input v-model="email" type="email" autocomplete="email" required />
        </Field>
        <Field :label="t('login.password')">
          <Input v-model="password" type="password" autocomplete="current-password" required />
        </Field>

        <Callout v-if="error" type="caution" :title="t('login.error')">{{ error }}</Callout>
        <Callout v-else-if="info" type="note" :title="t('login.checkEmail')">{{ info }}</Callout>

        <Button type="submit" :loading="loading">{{ t('login.submit') }}</Button>
      </form>

      <div class="flex flex-wrap justify-center gap-x-4 gap-y-2 text-sm">
        <RouterLink class="text-fg-secondary hover:text-fg" to="/register">{{ t('login.signUp') }}</RouterLink>
        <button
          class="cursor-pointer text-fg-secondary hover:text-fg"
          type="button"
          @click="forgot"
        >
          {{ t('login.forgot') }}
        </button>
      </div>
    </div>
  </AuthLayout>
</template>
