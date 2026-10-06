<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { MotionConfig } from 'motion-v'
import {
  ChatComposer,
  ChatMessage,
  ChatMorph,
  ChatThread,
  Markdown,
  PageTransition,
  ScrollIndicator,
  SidebarLayout,
  SidebarLayoutHeader,
  StatusText,
  ThemeToggle,
  Tour,
  TourStep,
} from 'elastic-ui'
import AppBreadcrumbs from './components/AppBreadcrumbs.vue'
import AppSidebar from './components/AppSidebar.vue'
import { isWaiting, profile, session } from './lib/auth.js'
import {
  activity,
  chatEnabled,
  loadChatEnabled,
  messages,
  open as chatOpen,
  responding,
  send,
  settled,
  sourceTitles,
} from './lib/chat.js'
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

// Whether the admin turned the chat on is read once, as soon as someone who has been let in is
// signed in: a person still waiting (or blocked) would only get a 403 from the settings.
watch(
  () => Boolean(session.value && profile.value && !isWaiting(profile.value)),
  (letIn) => letIn && chatEnabled.value === null && loadChatEnabled(),
  { immediate: true },
)

// A step on another page sends the tour there first, and `beforeStep` waits for the route to
// settle before the new target is measured. Tour calls this for its current step as soon as it
// mounts, open or not, so a reload would otherwise always jump to the first step's page.
function goToStep(meta) {
  if (tourOpen.value && meta.to && route.path !== meta.to) return router.push(meta.to)
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
         (HomeView's offerTour), kept in this browser as the other settings are. Each page is
         two steps, its tab then what's on it, so the jump reads as "follow this" rather than a
         sudden change of screen. -->
    <Tour v-if="withSidebar" v-model:open="tourOpen" :before-step="goToStep" @finish="closeTour">
      <TourStep target="home" to="/" :title="t('tour.home.title')">{{ t('tour.home.body') }}</TourStep>

      <TourStep target="nav-notes" :title="t('tour.notesTab.title')">{{ t('tour.notesTab.body') }}</TourStep>
      <TourStep target="new-note" to="/notes" :title="t('tour.notes.title')">{{ t('tour.notes.body') }}</TourStep>

      <template v-if="profile?.role === 'admin'">
        <TourStep target="nav-admin" :title="t('tour.adminTab.title')">{{ t('tour.adminTab.body') }}</TourStep>
        <TourStep target="admin" to="/admin" :title="t('tour.admin.title')">{{ t('tour.admin.body') }}</TourStep>
      </template>

      <TourStep target="nav-settings" :title="t('tour.settingsTab.title')">{{ t('tour.settingsTab.body') }}</TourStep>
      <TourStep target="settings" to="/settings" :title="t('tour.settings.title')">{{ t('tour.settings.body') }}</TourStep>
    </Tour>

    <!-- Honey, not the library's default: --aurora-1 to -4 are Kolmi's own, in style.css.
         Floats over every screen; an answer is whole, never streamed, so no ChatTool step. -->
    <ChatMorph
      v-if="withSidebar && chatEnabled"
      v-model:open="chatOpen"
      :label="t('chat.label')"
      :title="t('chat.title')"
      :settled="settled"
      :activity="activity"
    >
      <ChatThread>
        <!-- One child per message (ChatMessage, and the sources line when it has one), so
             ChatThread's "what was just added" glide sees one new thing, not two. -->
        <div v-for="m in messages" :key="m.id" class="flex flex-col gap-1.5">
          <!-- No `text` prop: the answer is Markdown, which ChatStream's plain-text wave can't
               draw, so the default slot takes over for both roles and the "thinking" line is
               drawn here instead of left to ChatMessage. -->
          <ChatMessage :role="m.role">
            <template v-if="m.role === 'user'">{{ m.text }}</template>
            <template v-else-if="m.error">
              <span class="text-[color:var(--color-danger)]">{{ m.error }}</span>
            </template>
            <StatusText v-else-if="!m.text" :text="m.status" working />
            <Markdown v-else :source="m.text" />
          </ChatMessage>
          <p v-if="m.sources?.length" class="m-0 text-meta text-fg-faint">
            {{ t('chat.sources', { pages: sourceTitles(m.sources) }) }}
          </p>
        </div>
      </ChatThread>
      <ChatComposer :placeholder="t('chat.placeholder')" :responding="responding" @send="send" />
    </ChatMorph>

    <ScrollIndicator ref="indicator" :class="tocShown && '2xl:hidden'" />
  </MotionConfig>
</template>
