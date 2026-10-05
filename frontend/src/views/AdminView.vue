<script setup>
import { computed, onMounted, provide, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, Collapsible, CollapsibleContent, CollapsibleTrigger, Empty, StatusText, TreeDrag } from 'elastic-ui'
import { Layers, Plus } from '@lucide/vue'
import AdminChat from '../components/AdminChat.vue'
import AdminClassLanguage from '../components/AdminClassLanguage.vue'
import AdminCreateDialog from '../components/AdminCreateDialog.vue'
import AdminPass from '../components/AdminPass.vue'
import AdminNode from '../components/AdminNode.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes } from '../lib/content.js'

// The whole tree, managed: create a section or a page at any level, rename,
// edit (description, icon, colour, on_home), move and reorder by dragging, and delete with a
// confirmation. The tree itself is AdminNode, recursive, read like folders and
// files. Below it, the class settings: the language the AI writes the pages in.
const { t } = useI18n()

const tree = ref([])
// The section a row was held over, or dropped into: its row opens to show it.
const revealed = ref(null)
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

// A row dropped somewhere: into its new parent if that changed, then the parent's children in
// their new order. Reads the tree before either call, so the order is the one that was drawn.
const relocate = guarded(async ({ id, parentId, index }) => {
  const node = allNodes.value.find((n) => n.id === id)
  const holder = parentId == null ? null : allNodes.value.find((n) => n.id === parentId)
  const ids = (holder ? (holder.children ?? []) : tree.value).map((n) => n.id).filter((x) => x !== id)
  ids.splice(index, 0, id)
  if ((node?.parent_id ?? null) !== parentId) await api.moveNode({ nodeId: id, parentId })
  revealed.value = parentId
  await api.reorderNodes({ ids })
})

provide('adminTree', {
  create: guarded((parentId, payload) => api.createNode({ parentId, ...payload })),
  update: guarded((nodeId, patch) => api.updateNode({ nodeId, ...patch })),
  remove: guarded((nodeId) => api.deleteNode({ nodeId })),
  allNodes,
  revealed,
})

onMounted(loadTree)
</script>

<template>
  <main class="py-16">
    <PageLayout data-tour="admin" :title="t('admin.title')" :lead="t('admin.lead')">
      <StatusText v-if="loading" :delay="300" :text="t('common.loadingContent')" working />

      <template v-else>
        <Callout v-if="error" type="caution" :title="t('common.somethingWrong')">{{ error }}</Callout>

        <!-- Each block folds, so a long tree does not push the class settings out of reach. -->
        <Collapsible default-open class="not-prose">
          <CollapsibleTrigger>{{ t('admin.content') }}</CollapsibleTrigger>
          <CollapsibleContent>
            <div class="flex flex-col gap-6 pt-4">
              <div class="flex justify-end">
                <AdminCreateDialog :parent-id="null">
                  <template #trigger>
                    <span class="inline-flex items-center gap-2">
                      <Plus class="size-4" />
                      {{ t('admin.addTop') }}
                    </span>
                  </template>
                </AdminCreateDialog>
              </div>

              <Empty
                v-if="tree.length === 0"
                :title="t('common.nothingHere')"
                :description="t('admin.empty')"
                :icon="Layers"
              />

              <TreeDrag v-else @move="(move) => relocate(move).catch(() => {})" @reveal="(id) => (revealed = id)">
                <ul class="flex flex-col gap-0.5">
                  <AdminNode
                    v-for="(node, i) in tree"
                    :key="node.id"
                    :node="node"
                    :siblings="tree"
                    :index="i"
                  />
                </ul>
              </TreeDrag>
            </div>
          </CollapsibleContent>
        </Collapsible>

        <!-- With the tree, not before it: shown while the tree loads, it was pushed down. -->
        <Collapsible id="class" default-open class="not-prose mt-8">
          <CollapsibleTrigger>{{ t('admin.classSettings') }}</CollapsibleTrigger>
          <CollapsibleContent>
            <div class="mt-2 flex flex-col divide-y divide-border border-y border-border">
              <AdminClassLanguage />
              <AdminPass />
              <AdminChat />
            </div>
          </CollapsibleContent>
        </Collapsible>
      </template>
    </PageLayout>
  </main>
</template>
