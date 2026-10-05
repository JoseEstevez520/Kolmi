<script setup>
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ActionButton, Button, Callout, Empty, Markdown, StatusText } from 'elastic-ui'
import { FileQuestion, FileText, Layers } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import PageFiles from '../components/PageFiles.vue'
import PageNav from '../components/PageNav.vue'
import { flatten, loadNode, loadNodes, nodes, pages, prefetchNode, trailTo } from '../lib/content.js'
import { downloadExport } from '../lib/export.js'
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
// The node is not there (deleted, or a link to one that never was).
const missing = ref(false)

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
const title = computed(() => {
  if (missing.value) return t('node.missing')
  return node.value?.title || (isPage.value ? t('node.page') : t('node.section'))
})
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

// Once a page is open, the others in its section are read in the background, a moment later so
// the page itself goes first. Over a real network each one waits on a round trip, which shows as
// "Loading…" at every step; read ahead, going to the next page finds it already here.
let readAheadTimer
function readAhead() {
  clearTimeout(readAheadTimer)
  readAheadTimer = setTimeout(() => {
    const level = trailTo(id.value, nodes.value).at(-1)?.level ?? []
    for (const sibling of level) if (sibling.id !== id.value) prefetchNode(sibling.id)
  }, 400)
}

async function load() {
  error.value = ''
  missing.value = false
  try {
    await loadNode(id.value)
    await loadNodes().catch(() => {})
    readAhead()
  } catch (e) {
    if (e.status === 404 || e.status === 422) missing.value = true
    else error.value = e.message || t('node.error')
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
    <PageLayout :title="title" :lead="lead" :toc="isPage">
      <template v-if="node && !isPage && children.length > 0" #actions>
        <ActionButton
          variant="ghost"
          icon="arrowDown"
          :label="t('export.section')"
          :done-label="t('export.done')"
          :error-label="t('export.error')"
          :action="() => downloadExport(id)"
        />
      </template>

      <Empty
        v-if="missing"
        :title="t('node.missingTitle')"
        :description="t('node.missingLong')"
        :icon="FileQuestion"
      >
        <template #actions>
          <Button variant="ghost" to="/">{{ t('node.backHome') }}</Button>
        </template>
      </Empty>

      <Callout
        v-else-if="error"
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
        <template v-else>
          <component
            :is="openui.Renderer"
            v-if="showWeb"
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
          <PageFiles :files="node?.files ?? []" />
          <PageNav :id="id" />
        </template>
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
