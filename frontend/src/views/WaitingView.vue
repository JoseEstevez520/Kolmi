<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, Callout, ConfirmButton, StatusText } from 'elastic-ui'
import AuthLayout from '../components/AuthLayout.vue'
import { api } from '../lib/api.js'
import { isWaiting, loadProfile, profile, signOut } from '../lib/auth.js'

// Where someone signed in but not let in ends up (the router sends them here): waiting for an
// admin to approve them, or blocked by one. They can check again, leave, or delete the account.
const router = useRouter()
const { t } = useI18n()

const blocked = computed(() => profile.value?.status === 'blocked')
const checking = ref(false)
const message = ref('')
const error = ref('')

async function checkAgain() {
  checking.value = true
  message.value = ''
  error.value = ''
  try {
    const current = await loadProfile(true)
    if (current && !isWaiting(current)) router.push('/')
    else message.value = t(blocked.value ? 'waiting.stillBlocked' : 'waiting.stillPending')
  } catch (e) {
    error.value = e.message || t('waiting.error')
  } finally {
    checking.value = false
  }
}

async function leave() {
  await signOut()
  router.push('/login')
}

// The square shows a failure itself; the reason is also written under the row.
async function deleteAccount() {
  error.value = ''
  try {
    await api.deleteMyAccount()
  } catch (e) {
    error.value = e.message || t('common.somethingWrongLong')
    throw e
  }
  await leave()
}
</script>

<template>
  <AuthLayout>
    <div class="flex flex-col gap-6">
      <Callout
        :type="blocked ? 'caution' : 'note'"
        :title="t(blocked ? 'waiting.blockedTitle' : 'waiting.pendingTitle')"
      >
        {{ t(blocked ? 'waiting.blocked' : 'waiting.pending') }}
      </Callout>

      <div class="flex flex-col gap-3">
        <Button :loading="checking" @click="checkAgain">{{ t('waiting.checkAgain') }}</Button>
        <Button variant="ghost" @click="leave">{{ t('waiting.signOut') }}</Button>
      </div>

      <StatusText v-if="message" :text="message" />
      <StatusText v-if="error" :text="error" error />

      <div class="flex items-center justify-between gap-4 border-t border-border pt-4">
        <div class="flex min-w-0 flex-col gap-0.5">
          <span class="text-label font-medium text-fg">{{ t('waiting.deleteTitle') }}</span>
          <span class="text-meta text-fg-muted">{{ t('waiting.deleteHint') }}</span>
        </div>
        <ConfirmButton
          variant="ghost"
          tone="danger"
          :label="t('waiting.delete')"
          :confirm-label="t('waiting.confirm')"
          :cancel-label="t('common.cancel')"
          :action="deleteAccount"
        />
      </div>
    </div>
  </AuthLayout>
</template>
