<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, Steps, StepsItem } from 'elastic-ui'
import { descendantIds, flatten } from '../../lib/content.js'
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

// Notes whose "seemed to belong here" hint is this node or anything under it. null while they
// load; false when they can't be read (not an admin, offline), and then the line is left out.
const noteCount = ref(null)
onMounted(async () => {
  if (isUser.value) return
  try {
    const ids = new Set([props.args.node_id, ...(node.value ? descendantIds(node.value) : [])])
    const notes = await data.loadNotes()
    noteCount.value = notes.filter((n) => ids.has(n.node_id)).length
  } catch {
    noteCount.value = false
  }
})

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
  const pages = below.filter((n) => n.kind === 'page').length
  const out = [{ title: node.value.title, body: t(node.value.kind === 'page' ? 'chat.preview.thePage' : 'chat.preview.theSection') }]
  if (below.length) {
    const names = below.slice(0, 3).map((n) => n.title).join(', ')
    const more = below.length > 3 ? t('chat.preview.andMore', { n: below.length - 3 }) : ''
    const count = pages ? t('chat.preview.pagesGo', { n: pages }, pages) : t('chat.preview.inside', { n: below.length }, below.length)
    out.push({ title: count, body: names + more })
  }
  // While the count comes (null) the step is simply not there yet: no text says it is counting.
  if (noteCount.value) out.push({ title: t('chat.preview.notesLose', { n: noteCount.value }, noteCount.value), body: t('chat.preview.notesStay') })
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
