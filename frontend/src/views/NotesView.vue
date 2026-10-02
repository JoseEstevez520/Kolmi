<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ActionButton,
  Callout,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Empty,
  Field,
  StatusText,
  Textarea,
} from 'elastic-ui'
import { NotebookPen } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { formatDate, noteStatusLabel } from '../lib/format.js'

const { t } = useI18n()

const content = ref('')
const notes = ref([])
const loading = ref(true)
const error = ref('')

// The outcome colour of each status, the library's own meaning for them: what
// needs care, what went well, what went wrong (elastic-ui USAGE 8).
const STATUS_TONES = {
  pending: 'var(--color-warning)',
  processed: 'var(--color-success)',
  discarded: 'var(--color-danger)',
}

const title = computed(() => (profile.value?.name ? t('notes.greeting', { name: profile.value.name }) : t('notes.title')))

async function load() {
  loading.value = true
  error.value = ''
  try {
    notes.value = await api.myNotes()
  } catch (e) {
    error.value = e.message || t('notes.errorLong')
  } finally {
    loading.value = false
  }
}

async function submit() {
  await api.createNote({ content: content.value.trim() })
  content.value = ''
  await load()
}

onMounted(load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title" :lead="t('notes.lead')">
      <Card>
        <CardHeader>
          <CardTitle>{{ t('notes.formTitle') }}</CardTitle>
          <CardDescription>
            {{ t('notes.formHint') }}
          </CardDescription>
        </CardHeader>
        <CardContent class="flex flex-col gap-3">
          <Field :label="t('notes.field')">
            <Textarea
              v-model="content"
              rows="4"
              :placeholder="t('notes.placeholder')"
            />
          </Field>
          <div class="flex justify-end">
            <ActionButton
              :action="submit"
              :disabled="!content.trim()"
              :label="t('notes.send')"
              :done-label="t('notes.sent')"
              :error-label="t('notes.sendError')"
              icon="plus"
            />
          </div>
        </CardContent>
      </Card>

      <h2 id="my-notes" class="mt-10">{{ t('notes.mine') }}</h2>

      <StatusText v-if="loading" :text="t('notes.loading')" working />
      <Callout v-else-if="error" type="caution" :title="t('notes.error')">
        {{ error }}
      </Callout>
      <Empty
        v-else-if="notes.length === 0"
        :title="t('notes.emptyTitle')"
        :description="t('notes.empty')"
        :icon="NotebookPen"
      />
      <CardGrid v-else>
        <PageCard
          v-for="note in notes"
          :key="note.id"
          :description="note.content"
          :meta="formatDate(note.created_at)"
          :status="noteStatusLabel(note.status)"
          :tone="STATUS_TONES[note.status]"
          clamp
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
