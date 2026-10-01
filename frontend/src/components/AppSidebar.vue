<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NavTree, NavTreeItem, Sidebar } from 'elastic-ui'
import { Home, LogOut, NotebookPen, Settings } from '@lucide/vue'
import { profile, signOut } from '../lib/auth.js'
import { loadNodes, nodes, rootOf } from '../lib/content.js'
import { nodeIcon } from '../lib/icons.js'

// The app's sidebar (elastic-ui "connected" variant): Home, Notes, the
// top-level nodes with their icon and colour (never the whole tree; the pages
// inside are reached from a section), the admin panel for admins, and sign out.
const route = useRoute()
const router = useRouter()

// Reading a node keeps its top-level section lit.
const active = computed(() => {
  if (route.name === 'node') {
    const root = rootOf(route.params.id)
    if (root) return `/node/${root.id}`
  }
  return route.path
})

onMounted(() => {
  loadNodes().catch(() => {})
})

async function handleSignOut() {
  await signOut()
  router.push('/login')
}
</script>

<template>
  <Sidebar variant="connected" label="Kolmi">
    <template #header>
      <RouterLink to="/" class="flex items-center gap-2 px-2.5 text-sm font-semibold text-fg">
        <img src="/logo.svg" alt="" width="18" height="18" />
        Kolmi
      </RouterLink>
    </template>

    <NavTree :model-value="active">
      <NavTreeItem value="/" to="/" :icon="Home">Home</NavTreeItem>
      <NavTreeItem value="/notes" to="/notes" :icon="NotebookPen">Notes</NavTreeItem>

      <NavTreeItem
        v-for="node in nodes"
        :key="node.id"
        :value="`/node/${node.id}`"
        :to="`/node/${node.id}`"
        :icon="nodeIcon(node)"
      >
        {{ node.title }}
      </NavTreeItem>

      <NavTreeItem v-if="profile?.role === 'admin'" value="/admin" to="/admin" :icon="Settings">
        Admin
      </NavTreeItem>
    </NavTree>

    <template #footer>
      <NavTree label="Account">
        <NavTreeItem value="/signout" :icon="LogOut" @click="handleSignOut">
          {{ profile ? `Sign out (${profile.name})` : 'Sign out' }}
        </NavTreeItem>
      </NavTree>
    </template>
  </Sidebar>
</template>
