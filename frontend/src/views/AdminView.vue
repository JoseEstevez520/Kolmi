<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { PageTransition, Tabs, TabsList, TabsTrigger } from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'

// The admin panel: a title, a selector for its pages (content, users, the class, bug reports) and the
// page itself below. Each page is its own route, so it can be linked and Back works; the selector
// is bound to the route, so it follows the address in both directions.
const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const SECTIONS = ['content', 'people', 'class', 'reports']

const section = computed({
  get: () => String(route.name).replace('admin-', ''),
  set: (value) => {
    if (SECTIONS.includes(value) && value !== section.value) router.push({ name: `admin-${value}` })
  },
})
</script>

<template>
  <main class="py-16">
    <PageLayout data-tour="admin" :title="t('admin.title')" :lead="section === 'content' ? '' : t(`admin.sections.${section}.lead`)">
      <!-- A page may put its own actions at the end of the selector's row (`#admin-actions`). -->
      <div class="not-prose mb-8 flex flex-wrap items-center justify-between gap-x-3">
        <Tabs v-model="section" variant="underline">
          <TabsList :aria-label="t('admin.title')">
            <TabsTrigger v-for="name in SECTIONS" :key="name" :value="name">
              {{ t(`admin.sections.${name}.tab`) }}
            </TabsTrigger>
          </TabsList>
        </Tabs>
        <div id="admin-actions" class="ml-auto flex items-center gap-1" />
      </div>

      <RouterView v-slot="{ Component, route: current }">
        <PageTransition :page="current.path">
          <component :is="Component" />
        </PageTransition>
      </RouterView>
    </PageLayout>
  </main>
</template>
