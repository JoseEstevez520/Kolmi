<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { Button, Callout, Sheet, SheetTitle, StatusText, TreeDrag } from 'elastic-ui'
import { Plus, Search } from '@lucide/vue'
import AdminCreateDialog from '../components/AdminCreateDialog.vue'
import AdminNode from '../components/AdminNode.vue'
import AdminPanel from '../components/AdminPanel.vue'
import AdminSearch from '../components/AdminSearch.vue'
import { api } from '../lib/api.js'
import { session } from '../lib/auth.js'
import { flatten, loadNodes } from '../lib/content.js'

// The content tree, managed. A master and its detail: the tree on the left, compact and folded,
// picks a node; the panel on the right does everything to the picked one (rename, add inside, edit,
// move, delete). Rows can still be dragged or moved with Alt and the arrows. The picked node
// lives in the address (`?node=ID`), so a reload and Back keep it; what is open is kept in this
// tab's session. On a phone the tree has the whole width and the panel opens as a sheet. It is one
// of the admin's pages (AdminView holds the title and the selector).
const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const tree = ref([])
const loading = ref(true)
const ready = ref(false)
const error = ref('')

// Every change runs here: it talks to the backend, reloads the tree and, if it
// fails, leaves the reason for the page to show. It rethrows so the button that
// started it (ActionButton, ConfirmButton) can show its own error.
function guarded(fn) {
  return async (...args) => {
    error.value = ''
    try {
      await fn(...args)
      await loadTree()
    } catch (e) {
      error.value = e.message || t('common.somethingWrongLong')
      throw e
    }
  }
}

async function loadTree() {
  if (!ready.value) loading.value = true
  error.value = ''
  try {
    tree.value = await loadNodes(true)
    ready.value = true
  } catch (e) {
    error.value = e.message || t('common.contentErrorLong')
  } finally {
    loading.value = false
  }
}

const allNodes = computed(() => flatten(tree.value))
const byId = computed(() => new Map(allNodes.value.map((node) => [String(node.id), node])))

// A row dropped somewhere: into its new parent if that changed, then the parent's children in
// their new order. Reads the tree before either call, so the order is the one that was drawn.
const relocate = guarded(async ({ id, parentId, index }) => {
  const node = allNodes.value.find((n) => n.id === id)
  const holder = parentId == null ? null : allNodes.value.find((n) => n.id === parentId)
  const ids = (holder ? (holder.children ?? []) : tree.value).map((n) => n.id).filter((x) => x !== id)
  ids.splice(index, 0, id)
  if ((node?.parent_id ?? null) !== parentId) await api.moveNode({ nodeId: id, parentId })
  reveal(parentId)
  await api.reorderNodes({ ids })
})

// A row moved by hand or with the keys is drawn again somewhere else: the focus, if it was on a
// row, goes back to it.
async function moved(move) {
  const had = document.activeElement?.closest?.('[role="treeitem"]')?.dataset.node
  await relocate(move).catch(() => {})
  if (had == null) return
  await nextTick()
  document.querySelector(`[role="treeitem"][data-node="${had}"]`)?.focus({ preventScroll: true })
}

// What is open, kept per person in this tab. Nothing is open until the admin opens it, apart from
// the way down to the picked node.
const OPEN_KEY = 'kolmi.admin.open.'
const opened = ref(new Set())

function storageKey() {
  return OPEN_KEY + (session.value?.user?.id ?? '')
}

function readOpened() {
  try {
    const stored = JSON.parse(sessionStorage.getItem(storageKey()))
    return new Set(Array.isArray(stored) ? stored.map(String) : [])
  } catch {
    return new Set()
  }
}

function keepOpened() {
  try {
    sessionStorage.setItem(storageKey(), JSON.stringify([...opened.value]))
  } catch {
    // Storage blocked or full: the tree just starts folded next time.
  }
}

const isOpen = (id) => opened.value.has(String(id))

function toggle(id, open = !isOpen(id)) {
  const key = String(id)
  if (open === opened.value.has(key)) return
  if (open) opened.value.add(key)
  else opened.value.delete(key)
  keepOpened()
}

function reveal(id) {
  if (id != null) toggle(id, true)
}

// The picked node is in the address. Picking pushes, so Back goes to the one before.
const selectedId = computed(() => {
  const node = route.query.node
  return typeof node === 'string' && node ? node : null
})
const selected = computed(() => (selectedId.value == null ? null : (byId.value.get(selectedId.value) ?? null)))

const wide = ref(true)
const sheetOpen = ref(false)
// The node whose title is being written in the panel.
const editingId = ref(null)
watch(selectedId, (id) => {
  if (editingId.value !== id) editingId.value = null
})

function select(id, { replace = false } = {}) {
  const query = { ...route.query }
  if (id == null) delete query.node
  else query.node = String(id)
  if (String(id ?? '') !== String(selectedId.value ?? '')) router[replace ? 'replace' : 'push']({ query })
  if (id != null && !wide.value) sheetOpen.value = true
}

// The one row Tab reaches: the last one focused, else the picked one, else the first, as long as
// it is in view (not folded away inside a section).
const focusId = ref(null)
function inView(id) {
  const node = byId.value.get(String(id))
  if (!node) return false
  for (let up = byId.value.get(String(node.parent_id)); up; up = byId.value.get(String(up.parent_id))) {
    if (!isOpen(up.id)) return false
  }
  return true
}
const tabStop = computed(() =>
  [focusId.value, selectedId.value, tree.value[0]?.id].map((id) => (id == null ? null : String(id))).find((id) => id != null && inView(id)),
)

// WAI-ARIA tree: up and down through the rows in view, Home and End, Right opens (then goes in),
// Left closes (then goes out), Space picks, Enter picks and, on the picked one, renames it, as F2
// does. Alt with the arrows is TreeDrag's (it moves the row), so it is left alone here.
function onTreeKey(event) {
  const row = event.target
  if (event.altKey || event.ctrlKey || event.metaKey || row.getAttribute?.('role') !== 'treeitem') return
  const rows = [...event.currentTarget.querySelectorAll('[role="treeitem"]')]
  const at = rows.indexOf(row)
  const node = byId.value.get(row.dataset.node)
  if (!node) return
  const folds = node.kind === 'section' && (node.children?.length ?? 0) > 0
  let next
  if (event.key === 'ArrowDown') next = rows[at + 1]
  else if (event.key === 'ArrowUp') next = rows[at - 1]
  else if (event.key === 'Home') next = rows[0]
  else if (event.key === 'End') next = rows.at(-1)
  else if (event.key === 'ArrowRight') {
    if (folds && !isOpen(node.id)) toggle(node.id, true)
    else if (folds) next = rows[at + 1]
  } else if (event.key === 'ArrowLeft') {
    if (folds && isOpen(node.id)) toggle(node.id, false)
    else next = rows.find((r) => r.dataset.node === String(node.parent_id))
  } else if (event.key === ' ') select(node.id)
  else if (event.key === 'Enter' || event.key === 'F2') {
    if (event.key === 'F2' || String(selectedId.value) === String(node.id)) editingId.value = String(node.id)
    select(node.id)
  } else return
  event.preventDefault()
  next?.focus()
}

function onTreeFocus(event) {
  const row = event.target.closest?.('[role="treeitem"]')
  if (row) focusId.value = row.dataset.node
}

// The way down to the picked node opens when it is picked, or moved somewhere else, and the row
// is brought into view if it was out of it (found in the search, or an address opened afresh).
const trail = computed(() => (selected.value ? `${selected.value.id}:${selected.value.parent_id ?? ''}` : ''))
watch(
  trail,
  () => {
    for (let node = byId.value.get(String(selected.value?.parent_id)); node; node = byId.value.get(String(node.parent_id))) {
      reveal(node.id)
    }
    if (!selected.value) return
    const id = selected.value.id
    nextTick(() => document.querySelector(`[role="treeitem"][data-node="${id}"]`)?.scrollIntoView({ block: 'nearest' }))
  },
  { immediate: true },
)

// An address that points at nothing (the node was deleted, or never was) is cleaned up.
watch(
  () => [ready.value, selectedId.value, selected.value],
  () => {
    if (ready.value && selectedId.value != null && !selected.value) select(null, { replace: true })
  },
)

const remove = guarded((nodeId) => api.deleteNode({ nodeId }))

let made = null
const create = guarded(async (parentId, payload) => {
  made = await api.createNode({ parentId, ...payload })
})

provide('adminTree', {
  // What was made opens its place and is picked, so it is there to be filled in.
  create: async (parentId, payload) => {
    made = null
    await create(parentId, payload)
    reveal(parentId)
    if (made?.id != null) select(made.id)
  },
  update: guarded((nodeId, patch) => api.updateNode({ nodeId, ...patch })),
  move: guarded((nodeId, parentId) => api.moveNode({ nodeId, parentId })),
  // The node goes; the one that held it is picked, so the panel is never left on nothing.
  remove: async (nodeId) => {
    const node = byId.value.get(String(nodeId))
    await remove(nodeId)
    if (String(selectedId.value) === String(nodeId)) select(node?.parent_id ?? null, { replace: true })
  },
  rootNodes: tree,
  allNodes,
  byId,
  selectedId,
  select,
  isOpen,
  toggle,
  reveal,
  editingId,
  tabStop,
})

// Wide: the panel sits beside the tree. Narrow: it comes up as a sheet when a node is picked.
let query
const onWidth = () => (wide.value = query.matches)
onMounted(() => {
  opened.value = readOpened()
  query = matchMedia('(min-width: 1024px)')
  onWidth()
  query.addEventListener('change', onWidth)
  loadTree()
})
onBeforeUnmount(() => query?.removeEventListener('change', onWidth))

watch(wide, (isWide) => isWide && (sheetOpen.value = false))

const searching = ref(false)
</script>

<template>
  <div class="not-prose">
    <!-- The screen's two actions, in the row of the tabs (AdminView keeps the place). -->
    <Teleport defer to="#admin-actions">
      <template v-if="ready">
        <Button
          variant="ghost"
          size="icon"
          :icon="Search"
          :aria-label="t('admin.search')"
          :title="t('admin.search')"
          @click="searching = true"
        />
        <span :title="t('admin.addTop')" class="inline-flex">
          <AdminCreateDialog :parent-id="null" size="icon">
            <template #trigger>
              <Plus class="size-4" aria-hidden="true" />
              <span class="sr-only">{{ t('admin.addTop') }}</span>
            </template>
          </AdminCreateDialog>
        </span>
      </template>
    </Teleport>

    <StatusText v-if="loading" :delay="300" :text="t('common.loadingContent')" working />

    <template v-else>
      <Callout v-if="error" type="caution" :title="t('common.somethingWrong')" class="mb-6">{{ error }}</Callout>

      <div class="grid items-start gap-8 lg:grid-cols-[minmax(0,19rem)_minmax(0,1fr)]">
        <TreeDrag @move="moved" @reveal="reveal">
          <ul role="tree" :aria-label="t('admin.sections.content.tab')" class="flex flex-col gap-0.5" @keydown="onTreeKey" @focusin="onTreeFocus">
            <AdminNode v-for="(node, i) in tree" :key="node.id" :node="node" :siblings="tree" :index="i" :level="1" />
          </ul>
        </TreeDrag>

        <aside v-if="wide && selected" class="sticky top-[calc(var(--page-header-height)+1rem)]">
          <AdminPanel :key="selected.id" :node="selected" />
        </aside>
      </div>

      <!-- Opened from the tree, not from a button: its own is kept out of sight. -->
      <div v-if="!wide" class="sr-only" inert>
        <Sheet v-model:open="sheetOpen" side="bottom">
          <template #trigger />
          <SheetTitle class="sr-only">{{ selected?.title }}</SheetTitle>
          <AdminPanel v-if="selected" :key="selected.id" :node="selected" bare />
        </Sheet>
      </div>
    </template>

    <AdminSearch v-model:open="searching" :nodes="allNodes" :by-id="byId" @pick="select" />
  </div>
</template>
