<script setup>
import { computed, onMounted, provide, ref } from 'vue'
import { Callout, Empty, StatusText } from 'elastic-ui'
import { Layers, Plus } from '@lucide/vue'
import AdminCreateDialog from '../components/AdminCreateDialog.vue'
import AdminNode from '../components/AdminNode.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes } from '../lib/content.js'

// The whole tree, managed: create a section or a page at any level, rename,
// edit (description, icon, colour, on_home), move, reorder and delete with a
// confirmation. The tree itself is AdminNode, recursive, read like folders and
// files.
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
      error.value = e.message || 'Something went wrong.'
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
    error.value = e.message || 'Could not load the content.'
  } finally {
    loading.value = false
  }
}

const allNodes = computed(() => flatten(tree.value))

provide('adminTree', {
  create: guarded((parentId, payload) => api.createNode({ parentId, ...payload })),
  update: guarded((nodeId, patch) => api.updateNode({ nodeId, ...patch })),
  move: guarded((nodeId, parentId) => api.moveNode({ nodeId, parentId })),
  reorder: guarded((ids) => api.reorderNodes({ ids })),
  remove: guarded((nodeId) => api.deleteNode({ nodeId })),
  allNodes,
})

onMounted(loadTree)
</script>

<template>
  <main class="py-16">
    <PageLayout title="Admin" lead="Create, rename, edit, move, reorder and delete the content tree.">
      <StatusText v-if="loading" text="Loading the content…" working />

      <template v-else>
        <Callout v-if="error" type="caution" title="Something went wrong">{{ error }}</Callout>

        <div class="not-prose flex flex-col gap-6">
          <div class="flex justify-end">
            <AdminCreateDialog :parent-id="null" parent-title="the top level">
              <template #trigger>
                <span class="inline-flex items-center gap-2">
                  <Plus class="size-4" />
                  Add at the top level
                </span>
              </template>
            </AdminCreateDialog>
          </div>

          <Empty
            v-if="tree.length === 0"
            title="Nothing here yet"
            description="Create the first section or page to start building the content."
            :icon="Layers"
          />

          <ul v-else class="flex flex-col gap-0.5 rounded-[var(--radius-lg)] border border-border p-1.5">
            <AdminNode
              v-for="(node, i) in tree"
              :key="node.id"
              :node="node"
              :siblings="tree"
              :index="i"
            />
          </ul>
        </div>
      </template>
    </PageLayout>
  </main>
</template>
