<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, Steps, StepsItem } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// delete_node / delete_user: what goes with it, and that it cannot be undone.
const props = defineProps({
  tool: { type: String, default: 'delete_node' },
  args: { type: Object, default: () => ({}) },
})
const { t } = useI18n()
const data = usePreviewData()
const isUser = computed(() => props.tool === 'delete_user')
if (isUser.value) data.ensure.users()
else data.ensure.nodes()

const node = computed(() => flatten(data.nodes.value).find((n) => n.id === props.args.node_id))
const user = computed(() => data.users.value?.find((u) => String(u.id) === String(props.args.user_id)))

const steps = computed(() => {
  if (isUser.value) {
    if (!user.value) return null
    return [
      { title: user.value.name, body: user.value.email || t('chat.preview.theAccount') },
      { title: t('chat.preview.notes', { n: user.value.notes ?? 0 }, user.value.notes ?? 0), body: t('chat.preview.theirNotes') },
    ]
  }
  if (!node.value) return null
  const below = flatten(node.value.children ?? [])
  const out = [{ title: node.value.title, body: t(node.value.kind === 'page' ? 'chat.preview.thePage' : 'chat.preview.theSection') }]
  if (below.length) {
    const names = below.slice(0, 3).map((n) => n.title).join(', ')
    const more = below.length > 3 ? t('chat.preview.andMore', { n: below.length - 3 }) : ''
    out.push({ title: t('chat.preview.inside', { n: below.length }, below.length), body: names + more })
  }
  return out
})
</script>

<template>
  <div v-if="steps" class="flex flex-col gap-2">
    <Steps static>
      <StepsItem v-for="s in steps" :key="s.title" :title="s.title">{{ s.body }}</StepsItem>
    </Steps>
    <Callout type="caution" :title="t('chat.preview.noUndoTitle')">{{ t('chat.preview.noUndo') }}</Callout>
  </div>
</template>
