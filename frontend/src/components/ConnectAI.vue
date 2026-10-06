<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  Card,
  CardContent,
  CodeBlock,
  ConfirmButton,
  CopyButton,
  Input,
  Logo,
  StatusText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  ToggleGroup,
  ToggleGroupItem,
  Tooltip,
  TruncatedText,
} from 'elastic-ui'
import { MessageSquareText, SquareTerminal } from '@lucide/vue'
import { siClaude, siCursor, siGooglegemini, siWindsurf } from 'simple-icons'
import openaiLogo from '../assets/logos/openai.svg'
import vscodeLogo from '../assets/logos/vscode.svg'
import { api } from '../lib/api.js'
import { formatDay } from '../lib/format.js'
import {
  CLI_CLIENTS,
  authHeader,
  cursorConfig,
  cursorLink,
  mcpServersJson,
  mcpUrl,
  vscodeJson,
  windsurfJson,
} from '../lib/mcp-clients.js'

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
// The picker: each client's logo (Simple Icons' entry, or a one-colour SVG for the two it lacks).
const PICKER = [
  { id: 'claude', icon: siClaude },
  { id: 'gemini', icon: siGooglegemini },
  { id: 'codex', src: openaiLogo },
  { id: 'cursor', icon: siCursor },
  { id: 'vscode', src: vscodeLogo },
  { id: 'windsurf', icon: siWindsurf },
  { id: 'other' },
  { id: 'agent' },
]
const client = ref('claude')
// Pressing the chosen client again would unpress it: keep it chosen instead.
function pick(value) {
  if (value) client.value = value
}
const cliClient = computed(() => CLI_CLIENTS.find((c) => c.id === client.value))

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
    client.value = 'claude'
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

      <Card size="sm">
        <CardContent class="flex items-center justify-between gap-2">
          <code class="min-w-0 break-all font-mono text-label text-fg">{{ token }}</code>
          <CopyButton :value="token" :label="t('settings.connect.copyToken')" />
        </CardContent>
      </Card>

      <ToggleGroup :model-value="client" @update:model-value="pick" type="single" class="self-start" :aria-label="t('settings.connect.pick')">
        <!-- No Tooltip around an item: its trigger would overwrite the item's data-state, which the
             group's sliding indicator reads. The native title is the hover name. -->
        <ToggleGroupItem
          v-for="item in PICKER"
          :key="item.id"
          :value="item.id"
          :title="t(`settings.connect.clients.${item.id}.name`)"
          :aria-label="t(`settings.connect.clients.${item.id}.name`)"
        >
          <Logo v-if="item.icon" :icon="item.icon" alt="" mono />
          <Logo v-else-if="item.src" :src="item.src" alt="" mono />
          <SquareTerminal v-else-if="item.id === 'other'" class="size-5" aria-hidden="true" />
          <MessageSquareText v-else class="size-5" aria-hidden="true" />
        </ToggleGroupItem>
      </ToggleGroup>

      <div class="flex flex-col gap-3">
        <h4 class="text-label font-medium text-fg">{{ t(`settings.connect.clients.${client}.name`) }}</h4>

        <template v-if="cliClient">
          <CodeBlock wrap :code="cliClient.lines(params).join('\n')" />
          <p class="text-meta text-fg-muted">{{ t(`settings.connect.clients.${client}.note`) }}</p>
        </template>

        <template v-else-if="client === 'cursor'">
          <div class="flex items-center gap-2">
            <Tooltip :content="t('settings.connect.clients.cursor.add')">
              <Button
                variant="ghost"
                size="icon"
                :href="cursorLink(params)"
                :aria-label="t('settings.connect.clients.cursor.add')"
              >
                <Logo :icon="siCursor" alt="" mono />
              </Button>
            </Tooltip>
            <p class="text-meta text-fg-muted">{{ t('settings.connect.clients.cursor.note') }}</p>
          </div>
          <CodeBlock wrap language="json" :code="cursorConfig(params)" />
        </template>

        <template v-else-if="client === 'vscode'">
          <CodeBlock wrap language="json" title=".vscode/mcp.json" :code="vscodeJson(params)" />
          <p class="text-meta text-fg-muted">{{ t('settings.connect.clients.vscode.note') }}</p>
        </template>

        <template v-else-if="client === 'windsurf'">
          <CodeBlock wrap language="json" title="mcp_config.json" :code="windsurfJson(params)" />
          <p class="text-meta text-fg-muted">{{ t('settings.connect.clients.windsurf.note') }}</p>
        </template>

        <template v-else-if="client === 'other'">
          <CodeBlock wrap :title="t('settings.connect.other.address')" :code="url" />
          <CodeBlock wrap :title="t('settings.connect.other.header')" :code="authHeader(token)" />
          <CodeBlock :title="t('settings.connect.other.file')" :code="mcpServersJson(params)" />
          <p class="text-meta text-fg-muted">{{ t('settings.connect.other.chatApps') }}</p>
        </template>

        <template v-else>
          <p class="text-label text-fg-secondary">{{ t('settings.connect.agent.hint') }}</p>
          <CodeBlock wrap :code="agentText" />
        </template>
      </div>

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
