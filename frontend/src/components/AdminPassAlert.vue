<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout } from 'elastic-ui'
import { api } from '../lib/api.js'
import { formatShortDate } from '../lib/format.js'

// The pass's health, at the top of the admin panel: shown only while its latest passes have all
// failed, gone once one works. Since when, why in plain words (the stored error on hover) and the
// notes waiting. `health` hands it the answer instead of asking (the /dev view).
const props = defineProps({ health: { type: Object, default: null } })
const { t } = useI18n()

const state = ref(props.health)

onMounted(async () => {
  if (props.health) return
  try {
    state.value = await api.passHealth()
  } catch {
    // Not knowing is no reason to warn: the AI log still shows every pass.
  }
})
</script>

<template>
  <Callout
    v-if="state?.status === 'failing'"
    type="warning"
    :title="t('admin.passAlert.title', { date: formatShortDate(state.since) })"
    class="not-prose mb-8"
  >
    <span :title="state.error || undefined">{{ t(`admin.passAlert.reasons.${state.reason}`) }}</span>
    {{ t('admin.passAlert.waiting', { n: state.pending }, state.pending) }}
  </Callout>
</template>
