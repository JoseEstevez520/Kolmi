<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  ConfirmButton,
  Empty,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Status,
  StatusText,
  TruncatedText,
} from 'elastic-ui'
import { Users } from '@lucide/vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { formatDay } from '../lib/format.js'

// The class's people: their role (a Select, saved at once), whether they were let in, and what
// an admin can do about it: approve someone pending, block or unblock, delete. Whoever is
// waiting comes first, then the rest by when they joined. A change the server refuses (the last
// admin, say) says why under the list, and the Select goes back to what it was.
const { t } = useI18n()

const users = ref([])
const loading = ref(true)
const loadError = ref('')
const error = ref('')
// The person a change is running for, so their row's buttons wait.
const busy = ref(null)
// Bumped when a role change fails, so the Selects are drawn again with the stored value.
const revert = ref(0)

// A status as the library's Status state: waiting stands out (needs a look), blocked is grey.
const STATUS_STATES = { active: 'done', pending: 'flagged', blocked: 'discarded' }
const ROLES = ['student', 'admin']

const sorted = computed(() =>
  [...users.value].sort(
    (a, b) =>
      Number(b.status === 'pending') - Number(a.status === 'pending') ||
      new Date(a.created_at) - new Date(b.created_at),
  ),
)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    users.value = await api.users()
  } catch (e) {
    loadError.value = e.message || t('admin.users.loadError')
  } finally {
    loading.value = false
  }
}

function replace(row) {
  users.value = users.value.map((u) => (u.id === row.id ? { ...u, ...row } : u))
}

async function change(user, call, onFail) {
  busy.value = user.id
  error.value = ''
  try {
    replace(await call())
  } catch (e) {
    error.value = e.message || t('common.somethingWrongLong')
    onFail?.()
    throw e
  } finally {
    busy.value = null
  }
}

function setRole(user, role) {
  if (role === user.role) return
  return change(user, () => api.setUserRole({ userId: user.id, role }), () => revert.value++).catch(() => {})
}

function setStatus(user, status) {
  return change(user, () => api.setUserStatus({ userId: user.id, status })).catch(() => {})
}

async function remove(user) {
  await change(user, async () => {
    await api.deleteUser({ userId: user.id })
    users.value = users.value.filter((u) => u.id !== user.id)
    return { id: user.id }
  })
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-4 pt-4">
    <p class="m-0 text-meta text-fg-muted">{{ t('admin.users.hint') }}</p>

    <StatusText v-if="loading" :delay="300" :text="t('admin.users.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />
    <Empty
      v-else-if="users.length === 0"
      :title="t('common.nothingHere')"
      :description="t('admin.users.empty')"
      :icon="Users"
    />

    <ul v-else :key="revert" class="m-0 flex list-none flex-col divide-y divide-border border-y border-border p-0">
      <li
        v-for="user in sorted"
        :key="user.id"
        class="grid gap-3 py-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center md:gap-6"
      >
        <div class="flex min-w-0 flex-col gap-1">
          <div class="flex min-w-0 items-center gap-2">
            <TruncatedText class="min-w-0 text-label font-medium text-fg">{{ user.name }}</TruncatedText>
            <span v-if="user.id === profile?.id" class="shrink-0 text-meta text-fg-faint">
              ({{ t('admin.users.you') }})
            </span>
          </div>
          <TruncatedText v-if="user.email" class="text-meta text-fg-muted">{{ user.email }}</TruncatedText>
          <span v-else class="text-meta text-fg-faint">{{ t('admin.users.noEmail') }}</span>
          <span class="text-meta text-fg-muted">
            {{ t('admin.users.joined', { date: formatDay(user.created_at) }) }} ·
            {{ t('admin.users.notes', { n: user.notes }, user.notes) }}
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
          <Select :model-value="user.role" class="w-36" @update:model-value="(role) => setRole(user, role)">
            <SelectTrigger :aria-label="t('admin.users.role', { name: user.name })">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="role in ROLES" :key="role" :value="role">
                {{ t(`admin.users.roles.${role}`) }}
              </SelectItem>
            </SelectContent>
          </Select>

          <Status
            class="w-28"
            :state="STATUS_STATES[user.status] ?? 'idle'"
            :label="t(`admin.users.status.${user.status}`)"
          />

          <div class="flex items-center gap-1 md:w-36 md:justify-end">
            <Button
              v-if="user.status === 'pending'"
              size="sm"
              :loading="busy === user.id"
              @click="setStatus(user, 'active')"
            >
              {{ t('admin.users.approve') }}
            </Button>
            <Button
              v-else-if="user.status === 'blocked'"
              variant="ghost"
              size="sm"
              :disabled="busy === user.id"
              @click="setStatus(user, 'active')"
            >
              {{ t('admin.users.unblock') }}
            </Button>
            <Button
              v-else
              variant="ghost"
              size="sm"
              :disabled="busy === user.id"
              @click="setStatus(user, 'blocked')"
            >
              {{ t('admin.users.block') }}
            </Button>
            <ConfirmButton
              variant="ghost"
              tone="danger"
              :label="t('admin.users.delete', { name: user.name })"
              :confirm-label="t('admin.users.confirmDelete')"
              :cancel-label="t('common.cancel')"
              :disabled="busy === user.id"
              :action="() => remove(user)"
            />
          </div>
        </div>
      </li>
    </ul>

    <StatusText v-if="error" :text="error" error />
  </div>
</template>
