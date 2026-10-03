<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Card, CardDescription, CardHeader, CardTitle, FileIcon } from 'elastic-ui'
import CardGrid from './CardGrid.vue'
import { downloadFile, formatSize } from '../lib/files.js'

// The page's files, at its end: drawn by the app from the page's own list, never written by
// the AI, so a file is never missing because a model forgot it. Each card is a link that asks
// for a short-lived download address when it is clicked. Nothing shows without files.
defineProps({
  files: { type: Array, default: () => [] },
})
const { t } = useI18n()
const error = ref('')

async function open(file) {
  error.value = ''
  try {
    await downloadFile(file.id)
  } catch (e) {
    error.value = e.message || t('files.downloadError')
  }
}
</script>

<template>
  <section v-if="files.length" class="not-prose mt-16 flex flex-col gap-3">
    <h2 class="text-meta font-normal text-fg-muted">{{ t('files.downloads') }}</h2>
    <CardGrid>
      <Card v-for="file in files" :key="file.id" href="#" size="sm" @click.prevent="open(file)">
        <CardHeader class="flex-row items-center gap-3">
          <FileIcon :name="file.name" />
          <div class="flex min-w-0 flex-col gap-0.5">
            <CardTitle size="sm" class="truncate">{{ file.name }}</CardTitle>
            <CardDescription>{{ formatSize(file.size) }}</CardDescription>
          </div>
        </CardHeader>
      </Card>
    </CardGrid>
    <p v-if="error" class="text-meta text-[color:var(--color-danger)]" role="alert">{{ error }}</p>
  </section>
</template>
