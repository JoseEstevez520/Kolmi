<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Callout, Empty, Markdown, StatusText } from 'elastic-ui'
import { Renderer } from '@openuidev/vue-lang'
import { FileText, Layers } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { flatten, loadNode, loadNodes, nodes, pages, prefetchNode } from '../lib/content.js'
import { iconByName } from '../lib/icons.js'
import { canRender, pageLibrary } from '../lib/openui/library.js'

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
// not parse into a page, the Markdown is shown instead.
const web = computed(() => node.value?.content_web?.trim() ?? '')
const showWeb = computed(() => canRender(web.value))
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
        <StatusText v-if="loadingContent" :delay="300" :text="t('common.loading')" working />
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
