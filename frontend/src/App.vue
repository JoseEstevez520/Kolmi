<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { MotionConfig } from 'motion-v'
import { PageTransition, ScrollIndicator, SidebarLayout, SidebarLayoutHeader, ThemeToggle, Tour, TourStep } from 'elastic-ui'
import AppBreadcrumbs from './components/AppBreadcrumbs.vue'
import AppSidebar from './components/AppSidebar.vue'
import { profile, session } from './lib/auth.js'
import { libraryLabels } from './lib/i18n.js'
import { motionOn } from './lib/motion.js'
import { tocShown } from './lib/toc.js'
import { closeTour, tourOpen } from './lib/tour.js'
import { zen } from './lib/zen.js'

// Inside the app, the elastic-ui shell (USAGE 12, 13 and 15): the sidebar, the
// page's own header with the theme toggle, and only the content changing
// between pages. Login and Register are a plain centred column instead. Zen mode
// is the layout gone bare: the sidebar and the header fold away, and nothing in
// the page is drawn again. The scroll line flashes on each new page, except at
// widths where the page shows its table of contents, which already marks where
// you are (hidden, not removed: the library hides the native bar while it is up).
const route = useRoute()
const router = useRouter()
const withSidebar = computed(() => route.meta.layout === 'app' && Boolean(session.value))

// A step on another page sends the tour there first, and `beforeStep` waits for the route to
// settle before the new target is measured.
function goToStep(meta) {
  if (meta.to && route.path !== meta.to) return router.push(meta.to)
}

// The app's own texts follow the language at once. elastic-ui reads its labels when each part
// is created, so the tree is keyed by the language and remounts when it changes.
const { t, locale } = useI18n()

const indicator = ref(null)
</script>

<template>
  <MotionConfig :reduced-motion="motionOn ? 'never' : 'always'">
    <SidebarLayout v-if="withSidebar" :bare="zen">
      <AppSidebar />

      <div class="min-w-0 flex-1">
        <SidebarLayoutHeader :toggle-label="t('app.openMenu')" class="shadow-none">
          <AppBreadcrumbs />
          <template #end>
            <!-- It stays through a language switch, and reads a default text only once. -->
            <ThemeToggle
              :light-label="libraryLabels.switchToLight"
              :dark-label="libraryLabels.switchToDark"
            />
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

    <!-- Walks the real screens, not just their sidebar links: a new account sees it once
         (HomeView's offerTour), kept in this browser as the other settings are. -->
    <Tour v-if="withSidebar" v-model:open="tourOpen" :before-step="goToStep" @finish="closeTour">
      <TourStep target="home" to="/" :title="t('tour.home.title')">{{ t('tour.home.body') }}</TourStep>
      <TourStep target="new-note" to="/notes" :title="t('tour.notes.title')">{{ t('tour.notes.body') }}</TourStep>
      <TourStep v-if="profile?.role === 'admin'" target="admin" to="/admin" :title="t('tour.admin.title')">
        {{ t('tour.admin.body') }}
      </TourStep>
      <TourStep target="settings" to="/settings" :title="t('tour.settings.title')">{{ t('tour.settings.body') }}</TourStep>
    </Tour>

    <ScrollIndicator ref="indicator" :class="tocShown && '2xl:hidden'" />
  </MotionConfig>
</template>
