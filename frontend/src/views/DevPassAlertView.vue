<script setup>
import { ThemeToggle } from 'elastic-ui'
import AdminPassAlert from '../components/AdminPassAlert.vue'
import PageLayout from '../components/PageLayout.vue'

// Development only (/dev/pass-alert): the admin panel's warning for a failing pass, with fake
// answers from pass_health and no API. The last one is a pass that works: nothing shows.
const ERROR_402 =
  "Error code: 402 - {'error': {'message': 'Insufficient Balance (request_id: 1cc0628c)', 'type': 'insufficient_balance_error', 'param': None, 'code': 'invalid_request_error'}}"
const CASES = [
  { status: 'failing', since: '2026-11-03T15:00:15Z', failed: 9, reason: 'credit', error: ERROR_402, pending: 3 },
  { status: 'failing', since: '2026-11-12T15:00:15Z', failed: 2, reason: 'quota', error: 'Error code: 429 - Rate limit reached', pending: 1 },
  { status: 'failing', since: '2026-11-16T15:00:15Z', failed: 1, reason: 'auth', error: 'Error code: 401 - Incorrect API key', pending: 12 },
  { status: 'failing', since: '2026-11-17T15:00:15Z', failed: 1, reason: 'other', error: 'Connection reset by peer', pending: 0 },
  { status: 'ok' },
]
</script>

<template>
  <main class="py-16">
    <PageLayout title="Admin">
      <div class="not-prose mb-8 flex justify-end"><ThemeToggle /></div>
      <AdminPassAlert v-for="(health, i) in CASES" :key="i" :health="health" />
    </PageLayout>
  </main>
</template>
