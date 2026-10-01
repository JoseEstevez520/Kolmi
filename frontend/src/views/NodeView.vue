<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Callout, Empty, Markdown, StatusText } from 'elastic-ui'
import { FileText, Layers } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { iconByName } from '../lib/icons.js'

// One node at /node/:id: a section shows its children as cards, a page shows
// its title and its Markdown (design.md, "Screens").
const route = useRoute()
const node = ref(null)
const loading = ref(true)
const error = ref('')

const isPage = computed(() => node.value?.kind === 'page')
const children = computed(() => node.value?.children ?? [])
const content = computed(() => node.value?.content_md?.trim() ?? '')
const title = computed(() => node.value?.title || (isPage.value ? 'Page' : 'Section'))
const lead = computed(() => {
  if (isPage.value) return ''
  const count = children.value.length
  return count === 1 ? '1 item' : count ? `${count} items` : ''
})

async function load() {
  loading.value = true
  error.value = ''
  node.value = null
  try {
    node.value = await api.node(route.params.id)
  } catch (e) {
    error.value = e.message || 'Could not load this node.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title" :lead="lead">
      <StatusText v-if="loading" text="Loading…" working />
      <Callout
        v-else-if="error"
        type="caution"
        :title="isPage ? 'Could not load this page' : 'Could not load this section'"
      >
        {{ error }}
      </Callout>

      <template v-else-if="isPage">
        <Markdown v-if="content" :source="content" />
        <Empty
          v-else
          title="Nothing here yet"
          description="This page has no content. The hive will fill it in."
          :icon="FileText"
        />
      </template>

      <template v-else>
        <Empty
          v-if="children.length === 0"
          title="Nothing here yet"
          description="This section has no pages or sections. An admin can add them."
          :icon="Layers"
        />
        <CardGrid v-else>
          <PageCard
            v-for="child in children"
            :key="child.id"
            :title="child.title"
            :description="child.description"
            :icon="iconByName(child.icon)"
            :color="child.color || 'var(--color-fg)'"
            :to="`/node/${child.id}`"
          />
        </CardGrid>
      </template>
    </PageLayout>
  </main>
</template>
