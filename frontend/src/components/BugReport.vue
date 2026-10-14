<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  DialogMorph,
  DialogMorphClose,
  DialogMorphTitle,
  Field,
  Input,
  Status,
  StatusText,
  Textarea,
} from 'elastic-ui'
import { api } from '../lib/api.js'
import { describeEnvironment } from '../lib/environment.js'

// Report a problem with the app. Rare and technical, so it hangs off Settings, not the sidebar.
// A report is judged in the background; the person's own reports below show where each ended up.
const { t } = useI18n()

const open = ref(false)
const title = ref('')
const body = ref('')
const sending = ref(false)
const sent = ref(false)
const error = ref('')
const reports = ref([])
const loadError = ref('')
let timer = null

// A report with no verdict yet is still being judged; one judged and waiting for an admin is
// flagged. Discarded is a decision, not an error: grey.
function stateOf(report) {
  if (report.status === 'issue') return 'done'
  if (report.status === 'discarded') return 'discarded'
  if (report.status === 'failed') return 'error'
  return report.reason ? 'flagged' : 'working'
}

const judging = computed(() => reports.value.some((r) => stateOf(r) === 'working'))

async function load() {
  try {
    reports.value = await api.myBugReports()
    loadError.value = ''
  } catch (e) {
    loadError.value = e.message || t('common.somethingWrongLong')
  }
}

// The judge takes a few seconds: look again until nothing is left to judge.
function watchJudging(times = 8) {
  clearTimeout(timer)
  if (times <= 0 || !open.value) return
  timer = setTimeout(async () => {
    await load()
    if (judging.value) watchJudging(times - 1)
  }, 3000)
}

watch(open, (isOpen) => {
  if (!isOpen) return clearTimeout(timer)
  title.value = ''
  body.value = ''
  sent.value = false
  error.value = ''
  load().then(() => judging.value && watchJudging())
})

onBeforeUnmount(() => clearTimeout(timer))

async function send() {
  if (!title.value.trim() || !body.value.trim()) return
  sending.value = true
  error.value = ''
  try {
    await api.reportBug({
      title: title.value.trim(),
      body: body.value.trim(),
      environment: describeEnvironment(),
    })
    sent.value = true
    title.value = ''
    body.value = ''
    await load()
    watchJudging()
  } catch (e) {
    error.value = e.status === 429 ? t('bug.limit') : e.message || t('common.somethingWrongLong')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <DialogMorph v-model:open="open" variant="ghost">
    <template #trigger>{{ t('bug.link') }}</template>

    <template #default>
      <DialogMorphTitle>{{ t('bug.title') }}</DialogMorphTitle>

      <form class="flex flex-col gap-4" @submit.prevent="send">
        <Field :label="t('bug.fieldTitle')">
          <Input v-model="title" maxlength="200" required />
        </Field>
        <Field :label="t('bug.fieldBody')">
          <Textarea v-model="body" rows="4" maxlength="5000" :placeholder="t('bug.bodyPlaceholder')" required />
        </Field>

        <p class="m-0 text-meta text-fg-faint">{{ t('bug.privacy') }}</p>

        <StatusText v-if="sent" :text="t('bug.sent')" />
        <StatusText v-if="error" :text="error" error />

        <div class="flex justify-end gap-2">
          <DialogMorphClose as-child>
            <Button variant="ghost">{{ t('common.cancel') }}</Button>
          </DialogMorphClose>
          <Button type="submit" variant="ghost" :loading="sending" :disabled="!title.trim() || !body.trim()">
            {{ t('bug.send') }}
          </Button>
        </div>
      </form>

      <section v-if="reports.length || loadError" class="mt-6 flex flex-col gap-3">
        <h3 class="text-label font-medium text-fg">{{ t('bug.mine') }}</h3>
        <StatusText v-if="loadError" :text="loadError" error />
        <ul class="flex max-h-60 flex-col gap-3 overflow-y-auto">
          <li v-for="report in reports" :key="report.id" class="flex flex-col gap-1">
            <span class="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
              <span class="min-w-0 truncate text-label text-fg">{{ report.title }}</span>
              <Status compact :state="stateOf(report)" :label="t(`bug.status.${report.status}`)" :reason="report.reason || undefined" />
            </span>
            <a
              v-if="report.issue_url"
              :href="report.issue_url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-label text-fg-secondary underline"
            >
              {{ t('bug.issue') }}
            </a>
            <p v-else-if="report.reason" class="text-label text-fg-secondary">{{ report.reason }}</p>
          </li>
        </ul>
      </section>
    </template>
  </DialogMorph>
</template>
