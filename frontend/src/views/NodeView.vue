<script setup>
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Callout, Empty, Markdown, StatusText } from 'elastic-ui'
import { FileText, Layers } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { flatten, loadNode, loadNodes, nodes, pages, prefetchNode } from '../lib/content.js'
import { iconByName } from '../lib/icons.js'
import { loadPageRenderer } from '../lib/openui/load.js'

// One node at /node/:id. The whole tree is already loaded, so a section paints
// its children at once; only a page's content needs a fetch, often done already
// when the link was pointed at (prefetchNode). The title shows meanwhile, and
// "Loading…" only if the wait is long enough to notice.
const route = useRoute()
const { t } = useI18n()
const id = computed(() => Number(route.params.id))

const error = ref('')

const cached = computed(() => flatten(nodes.value).find((node) => node.id === id.value) || null)
const node = computed(() => pages.value[id.value] ?? cached.value)

const isPage = computed(() => node.value?.kind === 'page')
const children = computed(() => node.value?.children ?? [])
const content = computed(() => node.value?.content_md?.trim() ?? '')
// The page's source is OpenUI Lang (see docs/page-format.md). When there is none, or it does
// not parse into a page, the Markdown is shown instead. The renderer is its own chunk, fetched
// the first time a page has a source; if it cannot be loaded, the page shows its Markdown.
const web = computed(() => node.value?.content_web?.trim() ?? '')
const openui = shallowRef(null)
const openuiFailed = ref(false)
const showWeb = computed(() => Boolean(openui.value?.canRender(web.value)))
const waitingRenderer = computed(() => Boolean(web.value) && !openui.value && !openuiFailed.value)
const title = computed(() => node.value?.title || (isPage.value ? t('node.page') : t('node.section')))
const loadingContent = computed(() => isPage.value && !(id.value in pages.value))

const lead = computed(() => {
  if (isPage.value) return ''
  const count = children.value.length
  return count ? t('node.items', { n: count }, count) : ''
})

// The renderer draws what it can and reports the rest; a page is still worth showing.
function onRenderErrors(errors) {
  if (errors.length) console.warn('Page source has errors:', errors)
}

watch(
  web,
  (source) => {
    if (!source || openui.value) return
    openuiFailed.value = false
    loadPageRenderer()
      .then((loaded) => (openui.value = loaded))
      .catch((e) => {
        console.warn('Could not load the page renderer:', e)
        openuiFailed.value = true
      })
  },
  { immediate: true },
)

async function load() {
  error.value = ''
  try {
    await loadNode(id.value)
  } catch (e) {
    error.value = e.message || t('node.error')
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
        :title="isPage ? t('node.pageError') : t('node.sectionError')"
      >
        {{ error }}
      </Callout>

      <template v-else-if="isPage">
        <StatusText
          v-if="loadingContent || waitingRenderer"
          :delay="300"
          :text="t('common.loading')"
          working
        />
        <component
          :is="openui.Renderer"
          v-else-if="showWeb"
          :key="id"
          :response="web"
          :library="openui.pageLibrary"
          :on-error="onRenderErrors"
        />
        <Markdown v-else-if="content" :source="content" />
        <Empty
          v-else
          :title="t('common.nothingHere')"
          :description="t('node.pageEmpty')"
          :icon="FileText"
        />
      </template>

      <template v-else>
        <StatusText v-if="!node" :delay="300" :text="t('common.loading')" working />
        <template v-else>
          <Empty
            v-if="children.length === 0"
            :title="t('common.nothingHere')"
            :description="t('node.sectionEmpty')"
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
              @pointerenter="prefetchNode(child.id)"
              @focusin="prefetchNode(child.id)"
            />
          </CardGrid>
        </template>
      </template>
    </PageLayout>
  </main>
</template>
