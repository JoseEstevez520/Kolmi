import { computed, ref } from 'vue'
import { api } from './api.js'

// The whole content tree, loaded once and shared. The sidebar lists only its
// roots; the admin panel refreshes it after every change, so the sidebar follows.
export const nodes = ref([])
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
      return nodes.value
    })
    .catch((error) => {
      nodesError.value = error.message || 'Could not load the content.'
      throw error
    })
    .finally(() => {
      nodesLoading.value = false
      inflight = null
    })

  return inflight
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
