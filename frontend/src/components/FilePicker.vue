<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileUpload } from 'elastic-ui'
import { api } from '../lib/api.js'
import { ACCEPT, MAX_FILE_BYTES, MAX_FILES_PER_NOTE } from '../lib/files.js'

// The files on one note or one page: the ones already there, and a picker to add more. A file
// is saved the moment it goes up, and taking it off the list deletes it on the server: there
// is no draft and no send. The list is elastic-ui's FileUpload; this only wires it to the API.
const props = defineProps({
  noteId: { type: Number, default: null },
  nodeId: { type: Number, default: null },
  // Until what the files hang from exists (a note not saved yet), the picker waits.
  disabled: { type: Boolean, default: false },
  dropLabel: { type: String, default: '' },
})
const emit = defineEmits(['change'])
const { t } = useI18n()

const rows = ref([])
const error = ref('')

// Which server file each row stands for. Loaded rows are keyed by their own id; a file just
// picked is known by the File object it came from, once it is up.
const serverIds = new Map()
const byFile = new WeakMap()
const idOf = (row) => serverIds.get(row.id) ?? (row.file && byFile.get(row.file))

async function load() {
  error.value = ''
  serverIds.clear()
  rows.value = []
  if (props.noteId == null && props.nodeId == null) return
  try {
    const files =
      props.noteId != null ? await api.noteFiles(props.noteId) : (await api.node(props.nodeId)).files ?? []
    rows.value = files.map((file) => {
      serverIds.set(`file-${file.id}`, file.id)
      return { id: `file-${file.id}`, name: file.name, size: file.size, status: 'done' }
    })
  } catch (e) {
    error.value = e.message || t('files.loadError')
  }
}
onMounted(load)
watch(() => [props.noteId, props.nodeId], load)

async function upload(file, onProgress) {
  error.value = ''
  const saved = await api.uploadFile({
    file,
    noteId: props.noteId,
    nodeId: props.nodeId,
    onProgress,
  })
  byFile.set(file, saved.id)
  emit('change')
}

// A row taken off the list: delete its file. If that fails, the row comes back.
let known = []
watch(rows, async (now) => {
  const gone = known.filter((row) => !now.some((r) => r.id === row.id))
  known = [...now]
  for (const row of gone) {
    const id = idOf(row)
    if (id == null) continue
    try {
      await api.deleteFile(id)
      emit('change')
    } catch (e) {
      error.value = e.message || t('files.removeError')
      rows.value = [...rows.value, row]
      known = [...rows.value]
    }
  }
})

const full = computed(
  () => props.noteId != null && rows.value.filter((r) => r.status !== 'error').length >= MAX_FILES_PER_NOTE,
)
const label = computed(() => {
  if (props.disabled) return props.dropLabel || t('files.attach')
  return full.value ? t('files.full', { n: MAX_FILES_PER_NOTE }) : props.dropLabel || t('files.attach')
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <FileUpload
      v-model="rows"
      :accept="ACCEPT"
      :max-size="MAX_FILE_BYTES"
      :upload="upload"
      :drop-label="label"
      :disabled="disabled || full"
    />
    <p v-if="error" class="text-meta text-[color:var(--color-danger)]" role="alert">{{ error }}</p>
  </div>
</template>
