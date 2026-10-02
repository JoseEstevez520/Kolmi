<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Callout, Empty, Markdown, StatusText } from 'elastic-ui'
import { Renderer } from '@openuidev/vue-lang'
import { FileText, Layers } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes, nodes } from '../lib/content.js'
import { iconByName } from '../lib/icons.js'
import { canRender, pageLibrary } from '../lib/openui/library.js'

// One node at /node/:id. The whole tree is already loaded, so a section paints
// its children at once; only a page's content needs a fetch, and the title
// shows meanwhile instead of blanking the page with a spinner.
const route = useRoute()
const id = computed(() => Number(route.params.id))

// Fetched nodes, kept so going back to a page is instant too.
const details = ref({})
const error = ref('')

const cached = computed(() => flatten(nodes.value).find((node) => node.id === id.value) || null)
const node = computed(() => details.value[id.value] ?? cached.value)

const isPage = computed(() => node.value?.kind === 'page')
const children = computed(() => node.value?.children ?? [])
const content = computed(() => node.value?.content_md?.trim() ?? '')
// The page's source is OpenUI Lang (see docs/page-format.md). When there is none, or it does
// not parse into a page, the Markdown is shown instead.
const web = computed(() => node.value?.content_web?.trim() ?? '')
const showWeb = computed(() => canRender(web.value))
const title = computed(() => node.value?.title || (isPage.value ? 'Page' : 'Section'))
const loadingContent = computed(() => isPage.value && !(id.value in details.value))

const lead = computed(() => {
  if (isPage.value) return ''
  const count = children.value.length
  return count === 1 ? '1 item' : count ? `${count} items` : ''
})

// The renderer draws what it can and reports the rest; a page is still worth showing.
function onRenderErrors(errors) {
  if (errors.length) console.warn('Page source has errors:', errors)
}

async function load() {
  error.value = ''
  if (id.value in details.value) return
  try {
    details.value[id.value] = await api.node(id.value)
  } catch (e) {
    error.value = e.message || 'Could not load this node.'
  }
}

onMounted(() => {
  loadNodes().catch(() => {})
  load()
})
watch(id, load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title" :lead="lead">
      <Callout
        v-if="error"
        type="caution"
        :title="isPage ? 'Could not load this page' : 'Could not load this section'"
      >
        {{ error }}
      </Callout>

      <template v-else-if="isPage">
        <StatusText v-if="loadingContent" text="Loading…" working />
        <Renderer
          v-else-if="showWeb"
          :key="id"
          :response="web"
          :library="pageLibrary"
          :on-error="onRenderErrors"
        />
        <Markdown v-else-if="content" :source="content" />
        <Empty
          v-else
          title="Nothing here yet"
          description="This page has no content. The hive will fill it in."
          :icon="FileText"
        />
      </template>

      <template v-else>
        <StatusText v-if="!node" text="Loading…" working />
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
      </template>
    </PageLayout>
  </main>
</template>
