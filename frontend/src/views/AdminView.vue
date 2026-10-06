<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { PageTransition, Tabs, TabsList, TabsTrigger } from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'

// The admin panel: a title, a selector for its three pages (content, users, the class) and the
// page itself below. Each page is its own route, so it can be linked and Back works; the selector
// is bound to the route, so it follows the address in both directions.
const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const SECTIONS = ['content', 'people', 'class']

const section = computed({
  get: () => String(route.name).replace('admin-', ''),
  set: (value) => {
    if (SECTIONS.includes(value) && value !== section.value) router.push({ name: `admin-${value}` })
  },
})
</script>

<template>
  <main class="py-16">
    <PageLayout data-tour="admin" :title="t('admin.title')" :lead="t(`admin.sections.${section}.lead`)">
      <Tabs v-model="section" variant="underline" class="not-prose mb-8">
        <TabsList :aria-label="t('admin.title')">
          <TabsTrigger v-for="name in SECTIONS" :key="name" :value="name">
            {{ t(`admin.sections.${name}.tab`) }}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <RouterView v-slot="{ Component, route: current }">
        <PageTransition :page="current.path">
          <component :is="Component" />
        </PageTransition>
      </RouterView>
    </PageLayout>
  </main>
</template>
