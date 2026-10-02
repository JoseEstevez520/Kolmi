<script setup>
import { computed, inject, ref } from 'vue'
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
  Textarea,
} from 'elastic-ui'
import { Settings2 } from '@lucide/vue'
import { descendantIds } from '../lib/content.js'
import { ICONS, ICON_NAMES, NODE_COLORS } from '../lib/icons.js'

// Edit one node: its title, description, icon, colour, whether it is on the
// home, and where it sits in the tree (move). Opened from the row's button.
const props = defineProps({
  node: { type: Object, required: true },
})

const admin = inject('adminTree')

const NONE = '__none__'
const ROOT = '__root__'
const GREY = '__grey__'

const title = ref(props.node.title)
const description = ref(props.node.description ?? '')
const icon = ref(props.node.icon || NONE)
const color = ref(props.node.color || GREY)
const onHome = ref(Boolean(props.node.on_home))
const parentId = ref(props.node.parent_id == null ? ROOT : String(props.node.parent_id))

const iconOptions = computed(() =>
  props.node.icon && !ICONS[props.node.icon] ? [props.node.icon, ...ICON_NAMES] : ICON_NAMES,
)

// The grey option carries no colour; a Select item needs a non-empty value, so
// it travels under a sentinel and is turned back into null on save.
const colorOptions = computed(() =>
  NODE_COLORS.map((option) => ({ ...option, value: option.value || GREY })),
)

// Any node but this one and its descendants can hold it.
const destinations = computed(() => {
  const excluded = new Set([props.node.id, ...descendantIds(props.node)])
  return admin.allNodes.value.filter((node) => !excluded.has(node.id))
})

async function save(close) {
  await admin.update(props.node.id, {
    title: title.value.trim() || props.node.title,
    description: description.value.trim(),
    icon: icon.value === NONE ? null : icon.value,
    color: color.value === GREY ? null : color.value,
    on_home: onHome.value,
  })
  const nextParent = parentId.value === ROOT ? null : Number(parentId.value)
  if (nextParent !== (props.node.parent_id ?? null)) {
    await admin.move(props.node.id, nextParent)
  }
  close()
}
</script>

<template>
  <DialogMorph variant="ghost" size="icon">
    <template #trigger>
      <Settings2 class="size-4" aria-hidden="true" />
      <span class="sr-only">Edit {{ node.title }}</span>
    </template>

    <template #default="{ close }">
      <DialogMorphTitle>Edit “{{ node.title }}”</DialogMorphTitle>

      <div class="flex flex-col gap-4">
        <Field label="Title">
          <Input v-model="title" />
        </Field>

        <Field label="Description" description="A line shown under the title on its card.">
          <Textarea v-model="description" rows="2" />
        </Field>

        <Field label="Icon">
          <Select v-model="icon">
            <SelectTrigger>
              <SelectValue placeholder="No icon" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="NONE">No icon</SelectItem>
              <SelectItem v-for="name in iconOptions" :key="name" :value="name">
                <span class="flex items-center gap-2">
                  <component
                    :is="ICONS[name]"
                    v-if="ICONS[name]"
                    class="size-4"
                    :stroke-width="1.5"
                  />
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

        <Field label="Parent" description="Where it sits in the tree.">
          <Select v-model="parentId">
            <SelectTrigger>
              <SelectValue placeholder="Top level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="ROOT">Top level</SelectItem>
              <SelectItem v-for="node in destinations" :key="node.id" :value="String(node.id)">
                {{ node.title }}
              </SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Switch v-model="onHome">Show on the home</Switch>

        <div class="flex justify-end gap-2">
          <DialogMorphClose as-child>
            <Button variant="ghost">Cancel</Button>
          </DialogMorphClose>
          <Button @click="save(close)">Save</Button>
        </div>
      </div>
    </template>
  </DialogMorph>
</template>
