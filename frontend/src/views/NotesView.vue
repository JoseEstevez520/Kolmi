<script setup>
import { computed, onMounted, ref } from 'vue'
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

const title = computed(() => (profile.value?.name ? `Hi, ${profile.value.name}` : 'Your notes'))

async function load() {
  loading.value = true
  error.value = ''
  try {
    notes.value = await api.myNotes()
  } catch (e) {
    error.value = e.message || 'Could not load your notes.'
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
    <PageLayout :title="title" lead="Leave a note; tonight the hive turns it into shared notes.">
      <Card>
        <CardHeader>
          <CardTitle>Leave a note</CardTitle>
          <CardDescription>
            Write it in your own words. It stays private until the daily pass.
          </CardDescription>
        </CardHeader>
        <CardContent class="flex flex-col gap-3">
          <Field label="Your note">
            <Textarea
              v-model="content"
              rows="4"
              placeholder="What did you learn today?"
            />
          </Field>
          <div class="flex justify-end">
            <ActionButton
              :action="submit"
              :disabled="!content.trim()"
              label="Send"
              done-label="Sent"
              error-label="Couldn't send"
              icon="plus"
            />
          </div>
        </CardContent>
      </Card>

      <h2 id="my-notes" class="mt-10">My notes</h2>

      <StatusText v-if="loading" text="Loading your notes…" working />
      <Callout v-else-if="error" type="caution" title="Could not load your notes">
        {{ error }}
      </Callout>
      <Empty
        v-else-if="notes.length === 0"
        title="The hive is quiet"
        description="Leave the first note; the daily pass will turn it into shared notes."
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
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
