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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tooltip,
  TruncatedText,
} from 'elastic-ui'
import { Ban, Check, Undo2, Users } from '@lucide/vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { formatDay } from '../lib/format.js'

// The class's people, as a table: who, whether they were let in, their role (a Select, saved at
// once) and when they joined, and an admin's quiet actions as icons:
// approve someone pending, block or unblock, delete. Whoever is waiting comes first, then the rest
// by when they joined. A change the server refuses (the last admin, say) says why under the
// table, and the Select goes back to what it was.
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

// The one status action a row offers: let a pending person in, unblock a blocked one, block anyone else.
function statusAction(user) {
  if (user.status === 'pending') return { status: 'active', icon: Check, key: 'approve' }
  if (user.status === 'blocked') return { status: 'active', icon: Undo2, key: 'unblock' }
  return { status: 'blocked', icon: Ban, key: 'block' }
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
    <StatusText v-if="loading" :delay="300" :text="t('admin.users.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />
    <Empty
      v-else-if="users.length === 0"
      :title="t('common.nothingHere')"
      :description="t('admin.users.empty')"
      :icon="Users"
    />

    <Table v-else :key="revert">
      <TableHeader>
        <TableRow>
          <TableHead>{{ t('admin.users.columns.person') }}</TableHead>
          <TableHead>{{ t('admin.users.columns.status') }}</TableHead>
          <TableHead>{{ t('admin.users.columns.role') }}</TableHead>
          <TableHead numeric>{{ t('admin.users.columns.joined') }}</TableHead>
          <TableHead><span class="sr-only">{{ t('admin.users.columns.actions') }}</span></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="user in sorted" :key="user.id">
          <TableCell>
            <!-- A set width: a long name or email is cut short, rather than widening the table. -->
            <div class="flex w-40 flex-col">
            <div class="flex min-w-0 items-baseline gap-1.5">
              <TruncatedText class="min-w-0 text-label text-fg">{{ user.name }}</TruncatedText>
              <span v-if="user.id === profile?.id" class="shrink-0 text-meta text-fg-faint">
                {{ t('admin.users.you') }}
              </span>
            </div>
            <TruncatedText v-if="user.email" class="text-meta text-fg-muted">{{ user.email }}</TruncatedText>
            <span v-else class="text-meta text-fg-faint">{{ t('admin.users.noEmail') }}</span>
            </div>
          </TableCell>
          <TableCell>
            <Status
              :state="STATUS_STATES[user.status] ?? 'idle'"
              :label="t(`admin.users.status.${user.status}`)"
            />
          </TableCell>
          <TableCell>
            <Select :model-value="user.role" class="w-32" @update:model-value="(role) => setRole(user, role)">
              <SelectTrigger :aria-label="t('admin.users.role', { name: user.name })">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="role in ROLES" :key="role" :value="role">
                  {{ t(`admin.users.roles.${role}`) }}
                </SelectItem>
              </SelectContent>
            </Select>
          </TableCell>
          <TableCell numeric class="text-fg-muted">{{ formatDay(user.created_at) }}</TableCell>
          <!-- Room on the right: the delete widens into its question in place, and must not be cut. -->
          <TableCell class="pr-6 max-sm:pr-24">
            <div class="flex items-center gap-1">
              <Tooltip :content="t(`admin.users.${statusAction(user).key}`, { name: user.name })">
                <Button
                  variant="ghost"
                  size="icon"
                  :icon="statusAction(user).icon"
                  :aria-label="t(`admin.users.${statusAction(user).key}`, { name: user.name })"
                  :disabled="busy === user.id"
                  @click="setStatus(user, statusAction(user).status)"
                />
              </Tooltip>
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
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>

    <StatusText v-if="error" :text="error" error />
  </div>
</template>
