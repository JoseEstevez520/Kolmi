<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NavTree, NavTreeGroup, NavTreeItem, Sidebar } from 'elastic-ui'
import { BookOpen, LogOut, NotebookPen, Settings } from '@lucide/vue'
import { profile, signOut } from '../lib/auth.js'
import { loadModules, modules } from '../lib/content.js'

// The app's sidebar (elastic-ui "connected" variant): Notes, the modules with
// their sections, the admin panel for admins, and sign out at the bottom.
const route = useRoute()
const router = useRouter()

// Reading a page keeps its section lit in the tree.
const active = computed(() =>
  route.name === 'page' ? `/sections/${route.params.sectionId}` : route.path,
)

onMounted(() => {
  loadModules().catch(() => {})
})

async function handleSignOut() {
  await signOut()
  router.push('/login')
}
</script>

<template>
  <Sidebar variant="connected" label="Kolmi">
    <template #header>
      <RouterLink to="/notes" class="flex items-center gap-2 px-2.5 text-sm font-semibold text-fg">
        <img src="/logo.svg" alt="" width="18" height="18" />
        Kolmi
      </RouterLink>
    </template>

    <NavTree :model-value="active">
      <NavTreeItem value="/notes" to="/notes" :icon="NotebookPen">Notes</NavTreeItem>

      <NavTreeGroup
        v-for="module in modules"
        :key="module.id"
        :label="module.name"
        :icon="BookOpen"
      >
        <NavTreeItem
          v-for="section in module.sections"
          :key="section.id"
          :value="`/sections/${section.id}`"
          :to="`/sections/${section.id}`"
        >
          {{ section.name }}
        </NavTreeItem>
      </NavTreeGroup>

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
