<script setup>
import { ref } from 'vue'
import { ActionButton, Field, Input } from 'elastic-ui'

// A small form to add a module, a section or a page: a name and a button that
// tells how it went.
const props = defineProps({
  label: { type: String, required: true },
  placeholder: { type: String, default: '' },
  buttonLabel: { type: String, required: true },
  add: { type: Function, required: true },
})

const value = ref('')

async function submit() {
  const name = value.value.trim()
  if (!name) return
  await props.add(name)
  value.value = ''
}
</script>

<template>
  <form class="flex items-end gap-2" @submit.prevent="submit">
    <Field :label="label" class="min-w-0 flex-1">
      <Input v-model="value" :placeholder="placeholder" />
    </Field>
    <ActionButton
      :action="submit"
      :disabled="!value.trim()"
      :label="buttonLabel"
      done-label="Added"
      error-label="Couldn't add"
      icon="plus"
    />
  </form>
</template>
