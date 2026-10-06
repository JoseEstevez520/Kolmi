<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  DialogMorph,
  DialogMorphClose,
  DialogMorphTitle,
  Field,
  IconPicker,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
} from 'elastic-ui'
import { FileText, Folder, Plus } from '@lucide/vue'
import { ICONS, NODE_COLORS } from '../lib/icons.js'

// Add a section or a page at any level: at the top level, or inside the node
// whose row opened it. A section is a folder, so it can be given its icon, its
// colour and whether it sits on the home from the start; a page only has a name.
const props = defineProps({
  parentId: { type: [Number, String], default: null },
  parentTitle: { type: String, default: '' },
  // The trigger's size: `icon` in a row of the tree, where only the icon shows.
  size: { type: String, default: 'md' },
})

const admin = inject('adminTree')
const { t } = useI18n()

const open = ref(false)
// At the top level only a section makes sense (the sidebar lists them); inside one, a page.
const defaultKind = () => (props.parentId == null ? 'section' : 'page')
const kind = ref(defaultKind())
const title = ref('')
const icon = ref(null)
const color = ref(null)
const onHome = ref(false)

const heading = computed(() =>
  props.parentId == null ? t('admin.addTop') : t('admin.addInsideOf', { title: props.parentTitle }),
)

// The colours on offer, named in the UI's language; grey is the neutral one (no colour).
const colorOptions = computed(() =>
  NODE_COLORS.map((option) => ({ value: option.value || null, label: t(`colors.${option.key}`) })),
)

function reset() {
  kind.value = defaultKind()
  title.value = ''
  icon.value = null
  color.value = null
  onHome.value = false
}

watch(open, (isOpen) => {
  if (isOpen) reset()
})

async function create(close) {
  const name = title.value.trim()
  if (!name) return
  const payload = { kind: kind.value, title: name }
  if (kind.value === 'section') {
    payload.icon = icon.value
    payload.color = color.value
    payload.onHome = onHome.value
  }
  await admin.create(props.parentId, payload)
  close()
}
</script>

<template>
  <DialogMorph v-model:open="open" variant="ghost" :size="size">
    <template #trigger>
      <slot name="trigger">
        <span class="inline-flex items-center gap-2">
          <Plus class="size-4" />
          {{ t('admin.addInside') }}
        </span>
      </slot>
    </template>

    <template #default="{ close }">
      <DialogMorphTitle>{{ heading }}</DialogMorphTitle>

      <div class="flex flex-col gap-4">
        <Field :label="t('admin.kind')">
          <Select v-model="kind">
            <SelectTrigger :aria-label="t('admin.kind')">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="section">
                <span class="flex items-center gap-2">
                  <Folder class="size-4 text-fg-muted" :stroke-width="1.5" aria-hidden="true" />
                  {{ t('admin.section') }}
                </span>
              </SelectItem>
              <SelectItem value="page">
                <span class="flex items-center gap-2">
                  <FileText class="size-4 text-fg-muted" :stroke-width="1.5" aria-hidden="true" />
                  {{ t('admin.page') }}
                </span>
              </SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Field :label="t('admin.fieldTitle')">
          <Input v-model="title" :placeholder="t('admin.titlePlaceholder')" />
        </Field>

        <template v-if="kind === 'section'">
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
        </template>

        <div class="flex justify-end gap-2">
          <DialogMorphClose as-child>
            <Button variant="ghost">{{ t('common.cancel') }}</Button>
          </DialogMorphClose>
          <Button variant="ghost" :disabled="!title.trim()" @click="create(close)">{{ t('common.add') }}</Button>
        </div>
      </div>
    </template>
  </DialogMorph>
</template>
