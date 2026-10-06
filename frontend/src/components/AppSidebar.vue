<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeItem, Sidebar } from 'elastic-ui'
import {
  CalendarDays,
  FileText,
  Folder,
  Home,
  LogOut,
  NotebookPen,
  ScrollText,
  Settings,
  SlidersHorizontal,
} from '@lucide/vue'
import { api } from '../lib/api.js'
import { profile, signOut } from '../lib/auth.js'
import { loadNodes, nodes, prefetchNode, trailTo } from '../lib/content.js'
import { libraryLabels } from '../lib/i18n.js'
import { nodeIcon } from '../lib/icons.js'

// The app's sidebar (elastic-ui "connected" variant): Home, Notes, the
// top-level nodes with their icon and colour (never the whole tree; the pages
// inside are reached from a section and the header's breadcrumbs), the admin
// panel for admins, and, at the bottom, Settings and sign out.
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// Reading a node keeps its top-level section lit, so the tab stays on the
// section while you move between its pages.
const active = computed(() => {
  if (route.name === 'node') {
    const root = trailTo(route.params.id, nodes.value)[0]?.node
    if (root) return `/node/${root.id}`
  }
  // The admin's three pages keep the Admin tab lit (the AI log has its own).
  if (route.path.startsWith('/admin/') && route.path !== '/admin/log') return '/admin'
  return route.path
})

// A node without an icon of its own gets a folder (section) or a sheet (page), so
// the rows keep their text aligned with Home and Notes.
function iconFor(node) {
  return nodeIcon(node) || (node.kind === 'section' ? Folder : FileText)
}

// Shown once an admin has turned the timetable on; an admin sees it regardless, since that
// page is also where it gets turned on in the first place.
const scheduleEnabled = ref(false)
const showSchedule = computed(() => scheduleEnabled.value || profile.value?.role === 'admin')

onMounted(() => {
  loadNodes().catch(() => {})
  api
    .settings()
    .then((settings) => (scheduleEnabled.value = settings.schedule_enabled))
    .catch(() => {})
})

async function handleSignOut() {
  await signOut()
  router.push('/login')
}
</script>

<template>
  <Sidebar variant="connected" label="Kolmi" :toggle-label="libraryLabels.toggleSidebar">
    <template #header>
      <RouterLink to="/" class="flex items-center gap-2 px-2.5 text-sm font-semibold text-fg">
        <img src="/logo.svg" alt="" width="18" height="18" />
        Kolmi
      </RouterLink>
    </template>

    <NavTree :model-value="active">
      <NavTreeItem value="/" to="/" :icon="Home">{{ t('sidebar.home') }}</NavTreeItem>
      <NavTreeItem value="/notes" to="/notes" :icon="NotebookPen" data-tour="nav-notes">{{ t('sidebar.notes') }}</NavTreeItem>
      <NavTreeItem v-if="showSchedule" value="/schedule" to="/schedule" :icon="CalendarDays">
        {{ t('sidebar.schedule') }}
      </NavTreeItem>

      <NavTreeItem
        v-for="node in nodes"
        :key="node.id"
        :value="`/node/${node.id}`"
        :to="`/node/${node.id}`"
        :icon="iconFor(node)"
        @pointerenter="prefetchNode(node.id)"
      >
        {{ node.title }}
      </NavTreeItem>

      <NavTreeItem v-if="profile?.role === 'admin'" value="/admin" to="/admin" :icon="Settings" data-tour="nav-admin">
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
        <NavTreeItem value="/settings" to="/settings" :icon="SlidersHorizontal" data-tour="nav-settings">
          {{ t('sidebar.settings') }}
        </NavTreeItem>
        <NavTreeItem value="/signout" :icon="LogOut" @click="handleSignOut">
          {{ profile ? t('sidebar.signOutAs', { name: profile.name }) : t('sidebar.signOut') }}
        </NavTreeItem>
      </NavTree>
    </template>
  </Sidebar>
</template>
