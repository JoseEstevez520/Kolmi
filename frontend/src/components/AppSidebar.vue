<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeItem, Sidebar } from 'elastic-ui'
import { Home, LogOut, NotebookPen, ScrollText, Settings, SlidersHorizontal } from '@lucide/vue'
import { profile, signOut } from '../lib/auth.js'
import { loadNodes, nodes, prefetchNode, rootOf } from '../lib/content.js'
import { nodeIcon } from '../lib/icons.js'

// The app's sidebar (elastic-ui "connected" variant): Home, Notes, the
// top-level nodes with their icon and colour (never the whole tree; the pages
// inside are reached from a section), the admin panel for admins, and, at the
// bottom, Settings and sign out.
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

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
      <NavTreeItem value="/" to="/" :icon="Home">{{ t('sidebar.home') }}</NavTreeItem>
      <NavTreeItem value="/notes" to="/notes" :icon="NotebookPen">{{ t('sidebar.notes') }}</NavTreeItem>

      <NavTreeItem
        v-for="node in nodes"
        :key="node.id"
        :value="`/node/${node.id}`"
        :to="`/node/${node.id}`"
        :icon="nodeIcon(node)"
        @pointerenter="prefetchNode(node.id)"
      >
        {{ node.title }}
      </NavTreeItem>

      <NavTreeItem v-if="profile?.role === 'admin'" value="/admin" to="/admin" :icon="Settings">
        {{ t('sidebar.admin') }}
      </NavTreeItem>

      <NavTreeItem
        v-if="profile?.role === 'admin'"
        value="/admin/log"
        to="/admin/log"
        :icon="ScrollText"
      >
        {{ t('sidebar.aiLog') }}
      </NavTreeItem>
    </NavTree>

    <template #footer>
      <NavTree :model-value="active" :label="t('sidebar.account')">
        <NavTreeItem value="/settings" to="/settings" :icon="SlidersHorizontal">
          {{ t('sidebar.settings') }}
        </NavTreeItem>
        <NavTreeItem value="/signout" :icon="LogOut" @click="handleSignOut">
          {{ profile ? t('sidebar.signOutAs', { name: profile.name }) : t('sidebar.signOut') }}
        </NavTreeItem>
      </NavTree>
    </template>
  </Sidebar>
</template>
