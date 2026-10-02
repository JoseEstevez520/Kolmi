<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Field, Input } from 'elastic-ui'
import AuthLayout from '../components/AuthLayout.vue'
import { api } from '../lib/api.js'
import { displayName, profile, session, signUp } from '../lib/auth.js'

const router = useRouter()
const { t } = useI18n()
const hasSession = computed(() => Boolean(session.value))

// Arriving from "Sign up", there is no session yet and the email and password
// are asked here too. After any first login, only the code and name are left.
const email = ref('')
const password = ref('')
const code = ref('')
const name = ref(displayName())
const error = ref('')
const notice = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  notice.value = ''
  loading.value = true
  try {
    if (!hasSession.value) {
      const newSession = await signUp(email.value.trim(), password.value)
      if (!newSession) {
        notice.value = t('register.confirmEmail')
        return
      }
    }
    profile.value = await api.register({ code: code.value.trim(), name: name.value.trim() })
    router.push('/')
  } catch (e) {
    error.value = e.message || t('register.errorLong')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <div class="flex flex-col gap-6">
      <form class="flex flex-col gap-4" @submit.prevent="submit">
        <template v-if="!hasSession">
          <Field :label="t('login.email')">
            <Input v-model="email" type="email" autocomplete="email" required />
          </Field>
          <Field :label="t('login.password')">
            <Input v-model="password" type="password" autocomplete="new-password" required />
          </Field>
        </template>

        <Field :label="t('register.classCode')" :description="t('register.classCodeHint')">
          <Input v-model="code" autocomplete="off" required />
        </Field>
        <Field :label="t('register.name')" :description="t('register.nameHint')">
          <Input v-model="name" autocomplete="name" required />
        </Field>

        <Callout v-if="error" type="caution" :title="t('register.error')">{{ error }}</Callout>
        <Callout v-else-if="notice" type="note" :title="t('login.checkEmail')">{{ notice }}</Callout>

        <Button type="submit" :loading="loading">{{ t('register.submit') }}</Button>
      </form>

      <p class="text-center text-sm">
        <RouterLink class="text-fg-secondary hover:text-fg" to="/login">{{ t('register.back') }}</RouterLink>
      </p>
    </div>
  </AuthLayout>
</template>
