<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Avatar, DescriptionItem, DescriptionList, Status } from 'elastic-ui'
import { ArrowRight } from '@lucide/vue'
import { usePreviewData } from '../../lib/previewData.js'

// set_status / set_role: who changes, from what to what. Admin only, so the people are read
// the first time such a proposal is shown.
const props = defineProps({
  tool: { type: String, default: 'set_status' },
  args: { type: Object, default: () => ({}) },
})
const { t } = useI18n()
const data = usePreviewData()
data.ensure.users()

// A status as the library's Status state, the same mapping as the admin's people list.
const STATES = { active: 'done', pending: 'flagged', blocked: 'discarded' }

const user = computed(() => data.users.value?.find((u) => String(u.id) === String(props.args.user_id)))
const change = computed(() => {
  if (!user.value) return null
  if (props.tool === 'set_role') {
    return {
      from: { state: 'idle', label: t(`admin.users.roles.${user.value.role}`) },
      to: { state: 'idle', label: t(`admin.users.roles.${props.args.role}`) },
    }
  }
  return {
    from: { state: STATES[user.value.status] ?? 'idle', label: t(`admin.users.status.${user.value.status}`) },
    to: { state: STATES[props.args.status] ?? 'idle', label: t(`admin.users.status.${props.args.status}`) },
  }
})
</script>

<template>
  <DescriptionList v-if="change">
    <DescriptionItem :term="user.name" class="py-1.5">
      <span class="flex items-center gap-3">
        <Avatar :name="user.name" size="sm" />
        <Status :state="change.from.state" :label="change.from.label" />
        <ArrowRight aria-hidden="true" class="size-4 text-fg-faint" />
        <Status :state="change.to.state" :label="change.to.label" />
      </span>
    </DescriptionItem>
  </DescriptionList>
</template>
