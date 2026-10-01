<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Callout, Empty, Markdown, StatusText } from 'elastic-ui'
import { FileText } from '@lucide/vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'

const route = useRoute()
const page = ref(null)
const loading = ref(true)
const error = ref('')

const title = computed(() => page.value?.title || 'Page')
const content = computed(() => page.value?.content_md?.trim() ?? '')

async function load() {
  loading.value = true
  error.value = ''
  page.value = null
  try {
    page.value = await api.page(route.params.pageId)
  } catch (e) {
    error.value = e.message || 'Could not load this page.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.pageId, load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title">
      <StatusText v-if="loading" text="Loading the page…" working />
      <Callout v-else-if="error" type="caution" title="Could not load this page">
        {{ error }}
      </Callout>
      <Markdown v-else-if="content" :source="content" />
      <Empty
        v-else
        title="Nothing here yet"
        description="This page has no content. The hive will fill it in."
        :icon="FileText"
      />
    </PageLayout>
  </main>
</template>
