<script setup>
import { onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeItem, Sidebar } from 'elastic-ui'
import { Home, LogOut, NotebookPen, ScrollText, Settings, SlidersHorizontal } from '@lucide/vue'
import { profile, signOut } from '../lib/auth.js'
import { loadNodes, nodes, trailTo } from '../lib/content.js'
import NavNode from './NavNode.vue'

// The app's sidebar (elastic-ui "connected" variant): Home, Notes, the whole
// tree (sections fold their pages, so the tab slides to the page being read),
// the admin panel for admins, and, at the bottom, Settings and sign out.
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// The sections on the way to the node being read open, so its tab shows; the
// ones opened by hand stay as they are.
const open = reactive({})
watch(
  () => (route.name === 'node' ? trailTo(route.params.id, nodes.value) : []),
  (trail) => trail.forEach(({ node }) => (open[node.id] = true)),
  { immediate: true },
)

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

    <NavTree :model-value="route.path">
      <NavTreeItem value="/" to="/" :icon="Home">{{ t('sidebar.home') }}</NavTreeItem>
      <NavTreeItem value="/notes" to="/notes" :icon="NotebookPen">{{ t('sidebar.notes') }}</NavTreeItem>

      <NavNode v-for="node in nodes" :key="node.id" :node="node" :open="open" top />

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
      <NavTree :model-value="route.path" :label="t('sidebar.account')">
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
