<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  DialogMorph,
  DialogMorphClose,
  DialogMorphTitle,
  Field,
  IconPicker,
  Input,
  Switch,
  Textarea,
} from 'elastic-ui'
import { Settings2 } from '@lucide/vue'
import FilePicker from './FilePicker.vue'
import { forgetNode } from '../lib/content.js'
import { ICONS, NODE_COLORS } from '../lib/icons.js'

// Edit one node: its title, description, icon, colour and whether it is on the
// home. Where it sits is changed by dragging its row. Opened from the row's button.
const props = defineProps({
  node: { type: Object, required: true },
})

const admin = inject('adminTree')
const { t } = useI18n()


const title = ref(props.node.title)
const description = ref(props.node.description ?? '')
const icon = ref(props.node.icon || null)
const color = ref(props.node.color || null)
const onHome = ref(Boolean(props.node.on_home))

// The colours on offer, named in the UI's language; grey is the neutral one (no colour).
const colorOptions = computed(() =>
  NODE_COLORS.map((option) => ({ value: option.value || null, label: t(`colors.${option.key}`) })),
)

async function save(close) {
  await admin.update(props.node.id, {
    title: title.value.trim() || props.node.title,
    description: description.value.trim(),
    icon: icon.value,
    color: color.value,
    on_home: onHome.value,
  })
  close()
}
</script>

<template>
  <DialogMorph variant="ghost" size="icon">
    <template #trigger>
      <Settings2 class="size-4" aria-hidden="true" />
      <span class="sr-only">{{ t('admin.edit', { title: node.title }) }}</span>
    </template>

    <template #default="{ close }">
      <DialogMorphTitle>{{ t('admin.editTitle', { title: node.title }) }}</DialogMorphTitle>

      <div class="flex flex-col gap-4">
        <Field :label="t('admin.fieldTitle')">
          <Input v-model="title" />
        </Field>

        <Field :label="t('admin.description')" :description="t('admin.descriptionHint')">
          <Textarea v-model="description" rows="2" />
        </Field>

        <Field :label="t('admin.iconAndColor')">
          <IconPicker
            v-model:icon="icon"
            v-model:color="color"
            :icons="ICONS"
            :colors="colorOptions"
            :label="t('admin.icon')"
            :none-label="t('admin.noIcon')"
          />
        </Field>

        <Switch v-model="onHome">{{ t('admin.onHome') }}</Switch>

        <Field v-if="node.kind === 'page'" :label="t('files.label')" :description="t('files.hint')">
          <FilePicker :node-id="node.id" @change="forgetNode(node.id)" />
        </Field>

        <div class="flex justify-end gap-2">
          <DialogMorphClose as-child>
            <Button variant="ghost">{{ t('common.cancel') }}</Button>
          </DialogMorphClose>
          <Button @click="save(close)">{{ t('common.save') }}</Button>
        </div>
      </div>
    </template>
  </DialogMorph>
</template>
