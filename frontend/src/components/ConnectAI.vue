<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  CodeBlock,
  ConfirmButton,
  Input,
  StatusText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  TruncatedText,
} from 'elastic-ui'
import { api } from '../lib/api.js'
import { formatDay } from '../lib/format.js'
import { CLI_CLIENTS, authHeader, mcpServersJson, mcpUrl } from '../lib/mcp-clients.js'

// Connecting your own AI to the class: a personal token, made here and shown once, and the exact
// text that puts it into each kind of client. The token lives only in this component's memory
// (`created`): never in storage, the URL or a log, and it is gone when "Done" is pressed or the
// page is left. The list below it never has the token, only its name and prefix.
const { t } = useI18n()

const url = mcpUrl()
const name = ref('')
const creating = ref(false)
const createError = ref('')
const created = ref(null)
const tab = ref('cli')

const tokens = ref([])
const loading = ref(true)
const loadError = ref('')
const revokeError = ref('')

const token = computed(() => created.value?.token ?? '')
const params = computed(() => ({ url, token: token.value }))
const agentText = computed(() => t('settings.connect.agent.text', { url, header: authHeader(token.value) }))

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    tokens.value = await api.tokens()
  } catch (e) {
    loadError.value = e.message || t('settings.connect.loadError')
  } finally {
    loading.value = false
  }
}

async function create() {
  const next = name.value.trim()
  if (!next) return
  creating.value = true
  createError.value = ''
  try {
    const made = await api.createToken({ name: next })
    // The list keeps the row without the token.
    const { token: _secret, ...row } = made
    tokens.value = [row, ...tokens.value]
    created.value = made
    tab.value = 'cli'
    name.value = ''
  } catch (e) {
    createError.value = e.message || t('common.somethingWrongLong')
  } finally {
    creating.value = false
  }
}

function done() {
  created.value = null
}

async function revoke(row) {
  revokeError.value = ''
  try {
    const answer = await api.revokeToken({ tokenId: row.id })
    tokens.value = tokens.value.map((x) =>
      x.id === row.id ? { ...x, revoked_at: answer?.revoked_at ?? new Date().toISOString() } : x,
    )
  } catch (e) {
    revokeError.value = e.message || t('common.somethingWrongLong')
    throw e
  }
}

onMounted(load)
onBeforeUnmount(() => {
  created.value = null
})
</script>

<template>
  <div class="flex flex-col">
    <h2 id="connect" class="mt-12 text-label font-medium text-fg">{{ t('settings.connect.title') }}</h2>

    <form
      v-if="!created"
      class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5"
      @submit.prevent="create"
    >
      <div class="flex min-w-0 max-w-sm flex-col gap-1">
        <h3 class="text-label font-medium text-fg">{{ t('settings.connect.make') }}</h3>
        <p class="text-label text-fg-secondary">{{ t('settings.connect.makeHint') }}</p>
      </div>
      <div class="flex w-full items-center gap-2 sm:w-80">
        <Input
          v-model="name"
          class="min-w-0 flex-1"
          :aria-label="t('settings.connect.nameLabel')"
          :placeholder="t('settings.connect.namePlaceholder')"
          maxlength="60"
          autocomplete="off"
          required
        />
        <Button type="submit" :loading="creating" :disabled="!name.trim()">
          {{ t('settings.connect.create') }}
        </Button>
      </div>
      <StatusText v-if="createError" class="w-full" :text="createError" error />
    </form>

    <section v-else class="flex flex-col gap-4 py-5" aria-live="polite">
      <div class="flex flex-col gap-1">
        <h3 class="text-label font-medium text-fg">{{ t('settings.connect.ready', { name: created.name }) }}</h3>
        <p class="text-label text-fg">{{ t('settings.connect.once') }}</p>
        <p class="text-label text-fg-secondary">{{ t('settings.connect.secret') }}</p>
      </div>

      <Tabs v-model="tab" variant="underline">
        <TabsList :aria-label="t('settings.connect.title')">
          <TabsTrigger value="cli">{{ t('settings.connect.tabs.cli') }}</TabsTrigger>
          <TabsTrigger value="other">{{ t('settings.connect.tabs.other') }}</TabsTrigger>
          <TabsTrigger value="agent">{{ t('settings.connect.tabs.agent') }}</TabsTrigger>
        </TabsList>

        <TabsContent value="cli" class="pt-4">
          <div class="flex flex-col gap-6">
            <div v-for="client in CLI_CLIENTS" :key="client.id" class="flex flex-col gap-2">
              <CodeBlock
                wrap
                :title="t(`settings.connect.clients.${client.id}.name`)"
                :code="client.lines(params).join('\n')"
              />
              <p class="text-meta text-fg-muted">{{ t(`settings.connect.clients.${client.id}.note`) }}</p>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="other" class="pt-4">
          <div class="flex flex-col gap-6">
            <CodeBlock wrap :title="t('settings.connect.other.address')" :code="url" />
            <CodeBlock wrap :title="t('settings.connect.other.header')" :code="authHeader(token)" />
            <CodeBlock :title="t('settings.connect.other.file')" :code="mcpServersJson(params)" />
            <p class="-mt-3 text-meta text-fg-muted">{{ t('settings.connect.other.chatApps') }}</p>
          </div>
        </TabsContent>

        <TabsContent value="agent" class="flex flex-col gap-3 pt-4">
          <p class="text-label text-fg-secondary">{{ t('settings.connect.agent.hint') }}</p>
          <CodeBlock wrap :title="t('settings.connect.tabs.agent')" :code="agentText" />
        </TabsContent>
      </Tabs>

      <div>
        <Button variant="ghost" class="-ml-4" @click="done">{{ t('settings.connect.done') }}</Button>
      </div>
    </section>

    <h3 class="mt-4 text-label font-medium text-fg">{{ t('settings.connect.yours') }}</h3>
    <div class="flex flex-col gap-3 py-4">
      <StatusText v-if="loading" :delay="300" :text="t('settings.connect.loading')" working />
      <StatusText v-else-if="loadError" :text="loadError" error />
      <p v-else-if="tokens.length === 0" class="text-label text-fg-muted">{{ t('settings.connect.none') }}</p>

      <Table v-else>
        <TableHeader>
          <TableRow>
            <TableHead>{{ t('settings.connect.columns.name') }}</TableHead>
            <TableHead class="max-sm:hidden">{{ t('settings.connect.columns.token') }}</TableHead>
            <TableHead numeric class="max-sm:hidden">{{ t('settings.connect.columns.created') }}</TableHead>
            <TableHead numeric>{{ t('settings.connect.columns.lastUsed') }}</TableHead>
            <TableHead><span class="sr-only">{{ t('settings.connect.columns.actions') }}</span></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="row in tokens" :key="row.id" :class="row.revoked_at && 'opacity-60'">
            <TableCell>
              <div class="flex w-24 flex-col sm:w-36">
                <TruncatedText class="text-label text-fg">{{ row.name }}</TruncatedText>
                <span v-if="row.revoked_at" class="text-meta text-fg-faint">{{ t('settings.connect.revoked') }}</span>
              </div>
            </TableCell>
            <TableCell class="font-mono text-meta text-fg-muted max-sm:hidden">{{ row.prefix }}…</TableCell>
            <TableCell numeric class="text-fg-muted max-sm:hidden">{{ formatDay(row.created_at) }}</TableCell>
            <TableCell numeric class="text-fg-muted">
              {{ row.last_used_at ? formatDay(row.last_used_at) : t('settings.connect.never') }}
            </TableCell>
            <!-- Room on the right: the revoke widens into its question in place, and must not be cut. -->
            <TableCell class="pr-6 max-sm:pr-20">
              <ConfirmButton
                v-if="!row.revoked_at"
                variant="ghost"
                tone="danger"
                :label="t('settings.connect.revoke', { name: row.name })"
                :confirm-label="t('settings.connect.revokeConfirm')"
                :cancel-label="t('common.cancel')"
                :action="() => revoke(row)"
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <StatusText v-if="revokeError" :text="revokeError" error />
    </div>
  </div>
</template>
