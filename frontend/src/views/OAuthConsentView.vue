<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Status } from 'elastic-ui'
import AuthLayout from '../components/AuthLayout.vue'
import { supabase } from '../lib/supabase.js'

const route = useRoute()
const { t } = useI18n()
const details = ref(null)
const error = ref('')
const busy = ref(false)
const id = typeof route.query.authorization_id === 'string' ? route.query.authorization_id : ''

async function decide(approve) {
  busy.value = true
  error.value = ''
  try {
    const method = approve ? 'approveAuthorization' : 'denyAuthorization'
    const result = await supabase.auth.oauth[method](id, { skipBrowserRedirect: true })
    if (result.error) throw result.error
    if (result.data?.redirect_url) window.location.assign(result.data.redirect_url)
  } catch (e) { error.value = e.message }
  finally { busy.value = false }
}
onMounted(async () => {
  try {
    if (!id) throw new Error(t('oauth.invalid'))
    const result = await supabase.auth.oauth.getAuthorizationDetails(id)
    if (result.error) throw result.error
    if (result.data?.redirect_url) window.location.assign(result.data.redirect_url)
    else details.value = result.data
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <AuthLayout>
    <div class="flex flex-col gap-4">
      <Callout v-if="error" type="caution">{{ error }}</Callout>
      <template v-if="details">
        <h2 class="text-title">{{ details.client.client_name }}</h2>
        <p>{{ t('oauth.access') }}</p>
        <p class="text-meta text-fg-muted">{{ details.scope }}</p>
        <div class="flex justify-end gap-2">
          <Button variant="ghost" :disabled="busy" @click="decide(false)">{{ t('oauth.deny') }}</Button>
          <Button :disabled="busy" @click="decide(true)">{{ t('oauth.allow') }}</Button>
        </div>
      </template>
      <Status v-else-if="!error" state="working" :label="t('oauth.loading')" />
    </div>
  </AuthLayout>
</template>
