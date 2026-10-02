import { computed, ref } from 'vue'
import { api } from './api.js'
import { t } from './i18n.js'

// The whole content tree, loaded once and shared. The sidebar lists only its
// roots; the admin panel refreshes it after every change, so the sidebar follows.
// The last tree seen is kept in this browser too, so opening the app paints it at
// once while the fresh one arrives (the tree is the same for everyone in a class).
const TREE_KEY = 'kolmi.tree'

function savedTree() {
  try {
    const saved = JSON.parse(localStorage.getItem(TREE_KEY) || 'null')
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

function keepTree(tree) {
  try {
    localStorage.setItem(TREE_KEY, JSON.stringify(tree))
  } catch {
    // Storage full or blocked: the next visit just waits for the tree.
  }
}

export const nodes = ref(savedTree())
export const nodesLoading = ref(false)
export const nodesError = ref('')

let loaded = false
let inflight = null

export function loadNodes(force = false) {
  if (loaded && !force) return Promise.resolve(nodes.value)
  if (inflight) return inflight

  nodesLoading.value = true
  nodesError.value = ''
  inflight = api
    .nodes()
    .then((data) => {
      nodes.value = Array.isArray(data) ? data : []
      loaded = true
      keepTree(nodes.value)
      // A change made in the admin panel may change a page too; read them again.
      if (force) pages.value = {}
      return nodes.value
    })
    .catch((error) => {
      nodesError.value = error.message || t('common.contentErrorLong')
      throw error
    })
    .finally(() => {
      nodesLoading.value = false
      inflight = null
    })

  return inflight
}

// A node with its content, read once per session: going back to a page is instant, and
// pointing at a link reads it ahead (prefetchNode) so the click finds it ready.
export const pages = ref({})
const pagesInflight = new Map()

export function loadNode(id) {
  if (id in pages.value) return Promise.resolve(pages.value[id])
  if (pagesInflight.has(id)) return pagesInflight.get(id)
  const request = api
    .node(id)
    .then((node) => {
      pages.value[id] = node
      return node
    })
    .finally(() => pagesInflight.delete(id))
  pagesInflight.set(id, request)
  return request
}

// Only a page has something to read ahead: a section is drawn from the tree.
export function prefetchNode(id) {
  const node = flatten().find((item) => item.id === id)
  if (node?.kind === 'page') loadNode(id).catch(() => {})
}

// The nodes the home grid shows.
export const homeNodes = computed(() => nodes.value.filter((node) => node.on_home))

// Every node in the tree, parents before children.
export function flatten(list = nodes.value) {
  const out = []
  const walk = (items) => {
    for (const item of items) {
      out.push(item)
      if (item.children?.length) walk(item.children)
    }
  }
  walk(list)
  return out
}

// The ids under a node, so it is never moved into itself.
export function descendantIds(node) {
  const out = []
  const walk = (item) => {
    for (const child of item.children ?? []) {
      out.push(child.id)
      walk(child)
    }
  }
  walk(node)
  return out
}

// The top-level node a node hangs from, so a page keeps its section lit in the
// sidebar. The tree is already loaded when the sidebar is up.
export function rootOf(id) {
  const target = Number(id)
  const walk = (item, root) => {
    if (Number(item.id) === target) return root
    for (const child of item.children ?? []) {
      const found = walk(child, root)
      if (found) return found
    }
    return null
  }
  for (const node of nodes.value) {
    const found = walk(node, node)
    if (found) return found
  }
  return null
}
