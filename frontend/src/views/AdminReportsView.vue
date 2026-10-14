<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ConfirmButton, Empty, Status, StatusText, TruncatedText } from 'elastic-ui'
import { Bug } from '@lucide/vue'
import { api } from '../lib/api.js'
import ListSkeleton from '../components/ListSkeleton.vue'
import { invalidate, useCached } from '../lib/cached.js'
import { formatShortDate } from '../lib/format.js'

// Every bug report of the class, newest first, for an admin: where each ended up and why, and the
// two things an admin can do with one that isn't filed yet: file it as an issue now (also when the
// judge discarded it or GitHub failed), or discard it. A filed one has only its link.
const { t } = useI18n()

// The last list draws at once and is fetched again quietly; "loading" is only for a first visit.
const { data, loading, error: failed, refresh } = useCached('adminReports')
const reports = computed(() => data.value ?? [])
const loadError = computed(() => (failed.value ? failed.value.trim() || t('admin.reports.loadError') : ''))
const error = ref('')
// The report a change is running for, so its buttons wait.
const busy = ref(null)

// Discarded is a decision, not an error: grey. A report with no verdict yet is still being judged.
function stateOf(report) {
  if (report.status === 'issue') return 'done'
  if (report.status === 'discarded') return 'discarded'
  if (report.status === 'failed') return 'error'
  return report.reason ? 'flagged' : 'working'
}

async function change(report, run) {
  busy.value = report.id
  error.value = ''
  try {
    await run()
    await invalidate('adminReports')
  } catch (e) {
    error.value = e.message || t('common.somethingWrongLong')
  } finally {
    busy.value = null
  }
}

const issueIt = (report) => change(report, () => api.fileBugReport({ id: report.id }))
const discard = (report) => change(report, () => api.discardBugReport({ id: report.id, reason: t('admin.reports.noReason') }))

onMounted(refresh)
</script>

<template>
  <div class="not-prose flex flex-col gap-4 pt-4">
    <ListSkeleton v-if="loading" />
    <StatusText v-else-if="loadError" :text="loadError" error />
    <Empty v-else-if="reports.length === 0" :title="t('common.nothingHere')" :description="t('admin.reports.empty')" :icon="Bug" />

    <ul v-else class="m-0 flex list-none flex-col divide-y divide-border p-0">
      <li v-for="report in reports" :key="report.id" class="flex items-start gap-4 py-3">
        <Status class="w-32 shrink-0 pt-px" :state="stateOf(report)" :label="t(`bug.status.${report.status}`)" />
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="text-label text-fg">{{ report.title }}</span>
          <span class="text-meta text-fg-muted">
            {{ report.author ? t('admin.reports.by', { name: report.author }) : t('admin.reports.unknownAuthor') }}
            · {{ formatShortDate(report.created_at) }}<template v-if="report.severity"> · {{ report.severity }}</template>
          </span>
          <TruncatedText v-if="report.reason" class="text-meta text-fg-muted">{{ report.reason }}</TruncatedText>
          <a
            v-if="report.issue_url"
            :href="report.issue_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-label text-fg-secondary underline"
          >
            {{ t('bug.issue') }}
          </a>
        </div>
        <!-- Room on the right: the confirm widens into its question in place, and must not be cut. -->
        <div v-if="report.status !== 'issue'" class="flex items-center gap-1 pr-6 max-sm:pr-24">
          <ConfirmButton
            variant="ghost"
            :label="t('admin.reports.issueIt')"
            :confirm-label="t('admin.reports.confirmIssue')"
            :cancel-label="t('common.cancel')"
            :disabled="busy === report.id"
            :action="() => issueIt(report)"
          />
          <ConfirmButton
            variant="ghost"
            tone="danger"
            :label="t('admin.reports.discard')"
            :confirm-label="t('admin.reports.confirmDiscard')"
            :cancel-label="t('common.cancel')"
            :disabled="busy === report.id"
            :action="() => discard(report)"
          />
        </div>
      </li>
    </ul>

    <StatusText v-if="error" :text="error" error />
  </div>
</template>
