<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Callout, Field, Input } from 'elastic-ui'
import AuthLayout from '../components/AuthLayout.vue'
import { api } from '../lib/api.js'
import { displayName, profile, session, signUp } from '../lib/auth.js'

const router = useRouter()
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
        notice.value =
          'We sent you an email. Confirm it, then sign in to finish setting up your account.'
        return
      }
    }
    profile.value = await api.register({ code: code.value.trim(), name: name.value.trim() })
    router.push('/')
  } catch (e) {
    error.value = e.message || 'Could not create your profile.'
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
          <Field label="Email">
            <Input v-model="email" type="email" autocomplete="email" required />
          </Field>
          <Field label="Password">
            <Input v-model="password" type="password" autocomplete="new-password" required />
          </Field>
        </template>

        <Field label="Class code" description="Ask your teacher for the code for this class.">
          <Input v-model="code" autocomplete="off" required />
        </Field>
        <Field label="Display name" description="This is the name your notes are shown under.">
          <Input v-model="name" autocomplete="name" required />
        </Field>

        <Callout v-if="error" type="caution" title="Could not join">{{ error }}</Callout>
        <Callout v-else-if="notice" type="note" title="Check your email">{{ notice }}</Callout>

        <Button type="submit" :loading="loading">Join the hive</Button>
      </form>

      <p class="text-center text-sm">
        <RouterLink class="text-fg-secondary hover:text-fg" to="/login">Back to sign in</RouterLink>
      </p>
    </div>
  </AuthLayout>
</template>
