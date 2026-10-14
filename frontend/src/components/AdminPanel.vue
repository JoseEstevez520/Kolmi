<script setup>
import { computed, inject, nextTick, onMounted, ref, useTemplateRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, ConfirmButton, Input, TruncatedText } from 'elastic-ui'
import { Check, Plus, X } from '@lucide/vue'
import AdminCreateDialog from './AdminCreateDialog.vue'
import AdminMovePicker from './AdminMovePicker.vue'
import AdminNodeDialog from './AdminNodeDialog.vue'
import NodeMark from './NodeMark.vue'

// What is done to the picked node: its title, written in place, and four icons: add inside (a
// section), edit, move to another section, delete. Beside the tree on a wide screen, in a sheet on
// a phone.
const props = defineProps({
  node: { type: Object, required: true },
  // In a sheet, which is already a surface of its own: no box inside it.
  bare: { type: Boolean, default: false },
})

const admin = inject('adminTree')
const { t } = useI18n()

const draft = ref(props.node.title)
const editing = computed(() => admin.editingId.value === String(props.node.id))

// The field takes the focus as it opens, from the title or from the tree's keys (Enter, F2).
const form = useTemplateRef('form')
const focusField = () =>
  nextTick(() => {
    const input = form.value?.querySelector('input')
    input?.focus()
    input?.select()
  })
watch(editing, (is) => {
  if (!is) return
  draft.value = props.node.title
  focusField()
})
onMounted(() => editing.value && focusField())

function start() {
  draft.value = props.node.title
  admin.editingId.value = String(props.node.id)
}

function cancel() {
  admin.editingId.value = null
}

async function save() {
  const title = draft.value.trim()
  cancel()
  if (!title || title === props.node.title) return
  try {
    await admin.update(props.node.id, { title })
  } catch {
    // The page says what went wrong.
  }
}
</script>

<template>
  <div :class="['flex flex-col gap-3', !bare && 'rounded-lg bg-bg-muted p-3']">
    <div class="flex min-w-0 items-center gap-2 pl-1.5">
      <NodeMark :node="node" class="shrink-0" />

      <form v-if="editing" ref="form" class="flex min-w-0 flex-1 items-center gap-1" @submit.prevent="save" @keydown.esc.stop="cancel">
        <Input v-model="draft" :aria-label="t('admin.rename')" />
        <Button type="submit" variant="ghost" size="icon" :icon="Check" :aria-label="t('common.save')" :title="t('common.save')" />
        <Button variant="ghost" size="icon" :icon="X" :aria-label="t('common.cancel')" :title="t('common.cancel')" @click="cancel" />
      </form>

      <h2 v-else class="m-0 flex min-w-0 flex-1 text-base font-medium">
        <!-- The button may shrink (a Button is shrink-0 by default), so a long title fades at its edge. -->
        <Button variant="link" class="min-w-0 flex-1 shrink justify-start text-fg" @click="start">
          <TruncatedText class="min-w-0">{{ node.title }}</TruncatedText>
        </Button>
      </h2>
    </div>

    <div class="flex items-center gap-1">
      <span v-if="node.kind === 'section'" :title="t('admin.addInsideOf', { title: node.title })" class="inline-flex">
        <AdminCreateDialog :parent-id="node.id" :parent-title="node.title" size="icon">
          <template #trigger>
            <Plus class="size-4" aria-hidden="true" />
            <span class="sr-only">{{ t('admin.addInsideOf', { title: node.title }) }}</span>
          </template>
        </AdminCreateDialog>
      </span>
      <span :title="t('admin.edit', { title: node.title })" class="inline-flex">
        <AdminNodeDialog :node="node" />
      </span>
      <span :title="t('admin.moveTo', { title: node.title })" class="inline-flex">
        <AdminMovePicker :node="node" />
      </span>
      <ConfirmButton
        variant="ghost"
        tone="danger"
        :label="t('admin.delete', { title: node.title })"
        :title="t('admin.delete', { title: node.title })"
        :action="() => admin.remove(node.id)"
      />
    </div>
  </div>
</template>
