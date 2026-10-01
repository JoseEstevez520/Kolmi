<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Callout, Empty, StatusText } from 'elastic-ui'
import { FileText } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'

const route = useRoute()
const section = ref(null)
const loading = ref(true)
const error = ref('')

const pages = computed(() => section.value?.pages ?? [])
const title = computed(() => section.value?.name || 'Section')
const lead = computed(() =>
  pages.value.length === 1 ? '1 page' : pages.value.length ? `${pages.value.length} pages` : '',
)

async function load() {
  loading.value = true
  error.value = ''
  section.value = null
  try {
    section.value = await api.section(route.params.sectionId)
  } catch (e) {
    error.value = e.message || 'Could not load this section.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.sectionId, load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title" :lead="lead">
      <StatusText v-if="loading" text="Loading the section…" working />
      <Callout v-else-if="error" type="caution" title="Could not load this section">
        {{ error }}
      </Callout>
      <Empty
        v-else-if="pages.length === 0"
        title="No pages yet"
        description="The hive hasn't written anything here yet."
        :icon="FileText"
      />
      <CardGrid v-else>
        <PageCard
          v-for="page in pages"
          :key="page.id"
          :title="page.title"
          :to="`/sections/${route.params.sectionId}/pages/${page.id}`"
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
