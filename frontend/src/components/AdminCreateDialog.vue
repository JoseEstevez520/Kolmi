<script setup>
import { computed, inject, ref, watch } from 'vue'
import {
  Button,
  DialogMorph,
  DialogMorphClose,
  DialogMorphTitle,
  Field,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
} from 'elastic-ui'
import { Plus } from '@lucide/vue'
import { ICONS, ICON_NAMES, NODE_COLORS } from '../lib/icons.js'

// Add a section or a page at any level: at the top level, or inside the node
// whose row opened it. A section is a folder, so it can be given its icon, its
// colour and whether it sits on the home from the start; a page only has a name.
const props = defineProps({
  parentId: { type: [Number, String], default: null },
  parentTitle: { type: String, default: '' },
})

const admin = inject('adminTree')

const NONE = '__none__'
const GREY = '__grey__'

const open = ref(false)
const kind = ref('page')
const title = ref('')
const icon = ref(NONE)
const color = ref(GREY)
const onHome = ref(false)

const heading = computed(() =>
  props.parentId == null ? 'Add at the top level' : `Add inside “${props.parentTitle}”`,
)

// The grey option carries no colour; a Select item needs a non-empty value, so
// it travels under a sentinel and is turned back into null on save.
const colorOptions = computed(() =>
  NODE_COLORS.map((option) => ({ ...option, value: option.value || GREY })),
)

function reset() {
  kind.value = 'page'
  title.value = ''
  icon.value = NONE
  color.value = GREY
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
    payload.icon = icon.value === NONE ? null : icon.value
    payload.color = color.value === GREY ? null : color.value
    payload.onHome = onHome.value
  }
  await admin.create(props.parentId, payload)
  close()
}
</script>

<template>
  <DialogMorph v-model:open="open">
    <template #trigger>
      <slot name="trigger">
        <span class="inline-flex items-center gap-2">
          <Plus class="size-4" />
          Add inside
        </span>
      </slot>
    </template>

    <template #default="{ close }">
      <DialogMorphTitle>{{ heading }}</DialogMorphTitle>

      <div class="flex flex-col gap-4">
        <Field label="Kind" description="A section groups; a page holds the content.">
          <Select v-model="kind">
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="section">Section</SelectItem>
              <SelectItem value="page">Page</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Field label="Title">
          <Input v-model="title" placeholder="Its name" />
        </Field>

        <template v-if="kind === 'section'">
          <Field label="Icon" description="Shown in the tree, the sidebar and its cards.">
            <Select v-model="icon">
              <SelectTrigger>
                <SelectValue placeholder="No icon" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem :value="NONE">No icon</SelectItem>
                <SelectItem v-for="name in ICON_NAMES" :key="name" :value="name">
                  <span class="flex items-center gap-2">
                    <component :is="ICONS[name]" class="size-4" :stroke-width="1.5" />
                    {{ name }}
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>
          </Field>

          <Field label="Colour" description="Only to tell sections apart.">
            <Select v-model="color">
              <SelectTrigger>
                <SelectValue placeholder="Grey" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="option in colorOptions" :key="option.name" :value="option.value">
                  <span class="flex items-center gap-2">
                    <span
                      class="size-3 shrink-0 rounded-full"
                      :style="{ background: option.value === GREY ? 'var(--color-fg)' : option.value }"
                    />
                    {{ option.name }}
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>
          </Field>

          <Switch v-model="onHome">Show on the home</Switch>
        </template>

        <div class="flex justify-end gap-2">
          <DialogMorphClose as-child>
            <Button variant="ghost">Cancel</Button>
          </DialogMorphClose>
          <Button :disabled="!title.trim()" @click="create(close)">Add</Button>
        </div>
      </div>
    </template>
  </DialogMorph>
</template>
