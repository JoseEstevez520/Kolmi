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
} from 'elastic-ui'
import { Plus } from '@lucide/vue'

// Add a section or a page at any level: at the top level, or inside the node
// whose row opened it. Opened from a row's button (or the panel's own).
const props = defineProps({
  parentId: { type: [Number, String], default: null },
  parentTitle: { type: String, default: '' },
})

const admin = inject('adminTree')

const kind = ref('page')
const title = ref('')

const heading = computed(() =>
  props.parentId == null ? 'Add at the top level' : `Add inside “${props.parentTitle}”`,
)

async function create(close) {
  const name = title.value.trim()
  if (!name) return
  await admin.create(props.parentId, kind.value, name)
  title.value = ''
  close()
}
</script>

<template>
  <DialogMorph>
    <template #trigger>
      <slot name="trigger">
        <Button variant="ghost" size="icon" aria-label="Add inside">
          <Plus class="size-4" />
        </Button>
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

        <div class="flex justify-end gap-2">
          <DialogMorphClose>Cancel</DialogMorphClose>
          <Button :disabled="!title.trim()" @click="create(close)">Add</Button>
        </div>
      </div>
    </template>
  </DialogMorph>
</template>
