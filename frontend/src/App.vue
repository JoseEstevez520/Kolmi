<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { MotionConfig } from 'motion-v'
import { PageTransition, ScrollIndicator, SidebarLayout, SidebarLayoutHeader, ThemeToggle } from 'elastic-ui'
import AppBreadcrumbs from './components/AppBreadcrumbs.vue'
import AppSidebar from './components/AppSidebar.vue'
import { session } from './lib/auth.js'
import { forceMotion } from './lib/motion.js'
import { tocShown } from './lib/toc.js'
import { zen } from './lib/zen.js'

// Inside the app, the elastic-ui shell (USAGE 12, 13 and 15): the sidebar, the
// page's own header with the theme toggle, and only the content changing
// between pages. Login and Register are a plain centred column instead. Zen mode
// is the layout gone bare: the sidebar and the header fold away, and nothing in
// the page is drawn again. The scroll line flashes on each new page, except at
// widths where the page shows its table of contents, which already marks where
// you are (hidden, not removed: the library hides the native bar while it is up).
const route = useRoute()
const withSidebar = computed(() => route.meta.layout === 'app' && Boolean(session.value))

// The app's own texts follow the language at once. elastic-ui reads its labels when each part
// is created, so the tree is keyed by the language and remounts when it changes.
const { t, locale } = useI18n()

const indicator = ref(null)
</script>

<template>
  <MotionConfig :key="locale" :reduced-motion="forceMotion ? 'never' : 'user'">
    <SidebarLayout v-if="withSidebar" :bare="zen">
      <AppSidebar />

      <div class="min-w-0 flex-1">
        <SidebarLayoutHeader :toggle-label="t('app.openMenu')" class="shadow-none">
          <AppBreadcrumbs />
          <template #end>
            <ThemeToggle />
          </template>
        </SidebarLayoutHeader>

        <main class="pt-4 pb-24">
          <RouterView v-slot="{ Component, route: current }">
            <PageTransition :page="current.meta.page ?? current.path" @changed="indicator?.flash()">
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

    <ScrollIndicator ref="indicator" :class="tocShown && '2xl:hidden'" />
  </MotionConfig>
</template>
