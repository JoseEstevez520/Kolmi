<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { MotionConfig } from 'motion-v'
import { PageTransition, ScrollIndicator, SidebarLayout, SidebarLayoutHeader, ThemeToggle } from 'elastic-ui'
import AppSidebar from './components/AppSidebar.vue'
import { session } from './lib/auth.js'
import { forceMotion } from './lib/motion.js'
import { zen } from './lib/zen.js'

// Inside the app, the elastic-ui shell (USAGE 12, 13 and 15): the sidebar, the
// page's own header with the theme toggle, and only the content changing
// between pages. Login and Register are a plain centred column instead. Zen mode
// is the layout gone bare: the sidebar and the header fold away, and nothing in
// the page is drawn again.
const route = useRoute()
const withSidebar = computed(() => route.meta.layout === 'app' && Boolean(session.value))

// The app's own texts follow the language at once. elastic-ui reads its labels when each part
// is created, so the tree is keyed by the language and remounts when it changes.
const { t, locale } = useI18n()
</script>

<template>
  <MotionConfig :key="locale" :reduced-motion="forceMotion ? 'never' : 'user'">
    <SidebarLayout v-if="withSidebar" :bare="zen">
      <AppSidebar />

      <div class="min-w-0 flex-1">
        <SidebarLayoutHeader :toggle-label="t('app.openMenu')" class="shadow-none">
          <span />
          <template #end>
            <ThemeToggle />
          </template>
        </SidebarLayoutHeader>

        <main class="pt-4 pb-24">
          <RouterView v-slot="{ Component, route: current }">
            <PageTransition :page="current.meta.page ?? current.path">
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
