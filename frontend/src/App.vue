<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { MotionConfig } from 'motion-v'
import { PageTransition, ScrollIndicator, SidebarLayout, SidebarLayoutHeader, ThemeToggle } from 'elastic-ui'
import AppSidebar from './components/AppSidebar.vue'
import LocaleToggle from './components/LocaleToggle.vue'
import { session } from './lib/auth.js'
import { zen } from './lib/zen.js'

// Inside the app, the elastic-ui shell (USAGE 12, 13 and 15): the sidebar, the
// page's own header with the theme toggle, and only the content changing
// between pages. Login and Register are a plain centred column instead. In zen
// mode the sidebar folds away to the left and the header fades up, with the
// library's glide; both stay mounted, so the note being written is not mounted
// again.
const route = useRoute()
const withSidebar = computed(() => route.meta.layout === 'app' && Boolean(session.value))

// The app's own texts follow the language at once. elastic-ui reads its labels when each part
// is created, so the tree is keyed by the language and remounts when it changes.
const { t, locale } = useI18n()
</script>

<template>
  <MotionConfig :key="locale" reduced-motion="user">
    <SidebarLayout v-if="withSidebar">
      <!-- A wrapper folds it: the Sidebar has two roots, so a v-show on it would do nothing. -->
      <div
        class="shrink-0 transition-[max-width,opacity] duration-500 ease-glide motion-reduce:transition-none"
        :class="zen ? 'pointer-events-none max-w-0 overflow-hidden opacity-0' : 'max-w-[20rem]'"
        :inert="zen"
      >
        <AppSidebar />
      </div>

      <div class="min-w-0 flex-1">
        <!-- The header keeps its place (and its stickiness) and only fades up out of sight. -->
        <SidebarLayoutHeader
          :toggle-label="t('app.openMenu')"
          class="shadow-none transition-[opacity,translate] duration-500 ease-glide motion-reduce:transition-none"
          :class="zen && 'pointer-events-none -translate-y-full opacity-0'"
          :inert="zen"
        >
          <span />
          <template #end>
            <div class="flex items-center gap-1">
              <LocaleToggle />
              <ThemeToggle />
            </div>
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
