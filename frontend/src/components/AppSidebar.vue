<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NavTree, NavTreeItem, Sidebar } from 'elastic-ui'
import { LogOut, NotebookPen } from '@lucide/vue'
import { profile, signOut } from '../lib/auth.js'

// The app's sidebar (elastic-ui "connected" variant): the one section that
// exists in phase 1, Notes, and sign out at the bottom.
const route = useRoute()
const router = useRouter()

const active = computed(() => (route.path.startsWith('/notes') ? '/notes' : ''))

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
