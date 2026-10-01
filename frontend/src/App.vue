<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { MotionConfig } from 'motion-v'
import { PageTransition, ScrollIndicator, SidebarLayout, SidebarLayoutHeader, ThemeToggle } from 'elastic-ui'
import AppSidebar from './components/AppSidebar.vue'
import { session } from './lib/auth.js'

// Inside the app, the elastic-ui shell (USAGE 12, 13 and 15): the sidebar, the
// page's own header with the theme toggle, and only the content changing
// between pages. Login and Register are a plain centred column instead.
const route = useRoute()
const withSidebar = computed(() => route.meta.layout === 'app' && Boolean(session.value))
</script>

<template>
  <MotionConfig reduced-motion="user">
    <SidebarLayout v-if="withSidebar">
      <AppSidebar />

      <div class="min-w-0 flex-1">
        <SidebarLayoutHeader toggle-label="Open the menu" class="shadow-none">
          <span />
          <template #end>
            <ThemeToggle />
          </template>
        </SidebarLayoutHeader>

        <main class="pt-4 pb-24">
          <RouterView v-slot="{ Component, route: current }">
            <PageTransition :page="current.path">
              <component :is="Component" />
            </PageTransition>
          </RouterView>
        </main>
      </div>
    </SidebarLayout>

    <RouterView v-else v-slot="{ Component, route: current }">
      <PageTransition :page="current.path">
        <component :is="Component" />
      </PageTransition>
    </RouterView>

    <ScrollIndicator />
  </MotionConfig>
</template>
