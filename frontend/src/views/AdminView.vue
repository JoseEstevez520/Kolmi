<script setup>
import { onMounted, ref } from 'vue'
import {
  Callout,
  Card,
  CardContent,
  CardHeader,
  Empty,
  Separator,
  StatusText,
} from 'elastic-ui'
import { Layers } from '@lucide/vue'
import AdminAdd from '../components/AdminAdd.vue'
import AdminRow from '../components/AdminRow.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { loadModules } from '../lib/content.js'

const tree = ref([])
const loading = ref(true)
const ready = ref(false)
const error = ref('')

// Every change runs here: it talks to the backend, reloads the tree and, if it
// fails, leaves the reason for the page to show. It rethrows so the button that
// started it (ActionButton, ConfirmButton) can show its own error.
function guarded(fn) {
  return async (...args) => {
    error.value = ''
    try {
      await fn(...args)
      await loadTree()
    } catch (e) {
      error.value = e.message || 'Something went wrong.'
      throw e
    }
  }
}

async function loadTree() {
  if (!ready.value) loading.value = true
  error.value = ''
  try {
    const list = await loadModules(true)
    const sections = list.flatMap((module) => module.sections ?? [])
    const details = await Promise.all(sections.map((section) => api.section(section.id)))
    const pagesBySection = new Map(details.map((section) => [section.id, section.pages ?? []]))
    tree.value = list.map((module) => ({
      ...module,
      sections: (module.sections ?? []).map((section) => ({
        ...section,
        pages: pagesBySection.get(section.id) ?? [],
      })),
    }))
    ready.value = true
  } catch (e) {
    error.value = e.message || 'Could not load the content.'
  } finally {
    loading.value = false
  }
}

const addModule = guarded((name) => api.createModule({ name }))
const renameModule = guarded((moduleId, name) => api.renameModule({ moduleId, name }))
const removeModule = guarded((moduleId) => api.deleteModule({ moduleId }))

async function reorderModules(index, delta) {
  const ids = tree.value.map((module) => module.id)
  const target = index + delta
  if (target < 0 || target >= ids.length) return
  ;[ids[index], ids[target]] = [ids[target], ids[index]]
  await api.reorderModules({ ids })
}
const moveModule = guarded(reorderModules)

const addSection = guarded((moduleId, name) => api.createSection({ moduleId, name }))
const renameSection = guarded((sectionId, name) => api.renameSection({ sectionId, name }))
const removeSection = guarded((sectionId) => api.deleteSection({ sectionId }))

async function reorderSections(module, index, delta) {
  const ids = module.sections.map((section) => section.id)
  const target = index + delta
  if (target < 0 || target >= ids.length) return
  ;[ids[index], ids[target]] = [ids[target], ids[index]]
  await api.reorderSections({ ids })
}
const moveSection = guarded(reorderSections)

const addPage = guarded((sectionId, title) => api.createPage({ sectionId, title }))
const renamePage = guarded((pageId, title) => api.renamePage({ pageId, title }))
const removePage = guarded((pageId) => api.deletePage({ pageId }))

async function reorderPages(section, index, delta) {
  const ids = section.pages.map((page) => page.id)
  const target = index + delta
  if (target < 0 || target >= ids.length) return
  ;[ids[index], ids[target]] = [ids[target], ids[index]]
  await api.reorderPages({ ids })
}
const movePage = guarded(reorderPages)

onMounted(loadTree)
</script>

<template>
  <main class="py-16">
    <PageLayout
      title="Admin"
      lead="Create, rename, reorder and delete modules, sections and pages."
    >
      <StatusText v-if="loading" text="Loading the content…" working />

      <template v-else>
        <Callout v-if="error" type="caution" title="Something went wrong">{{ error }}</Callout>

        <div class="not-prose flex flex-col gap-6">
          <AdminAdd
            label="New module"
            placeholder="Module name"
            button-label="Add module"
            :add="addModule"
          />

          <Empty
            v-if="tree.length === 0"
            title="No modules yet"
            description="Create the first module to start building the content."
            :icon="Layers"
          />

          <div v-else class="flex flex-col gap-6">
            <Card v-for="(module, mi) in tree" :key="module.id">
              <CardHeader>
                <AdminRow
                  :value="module.name"
                  :can-move-up="mi > 0"
                  :can-move-down="mi < tree.length - 1"
                  rename-label="Rename module"
                  delete-label="Delete module"
                  :rename="(name) => renameModule(module.id, name)"
                  :move-up="() => moveModule(mi, -1)"
                  :move-down="() => moveModule(mi, 1)"
                  :remove="() => removeModule(module.id)"
                />
              </CardHeader>

              <CardContent class="flex flex-col gap-4">
                <div
                  v-for="(section, si) in module.sections"
                  :key="section.id"
                  class="flex flex-col gap-3 border-l border-border pl-4"
                >
                  <AdminRow
                    :value="section.name"
                    :can-move-up="si > 0"
                    :can-move-down="si < module.sections.length - 1"
                    rename-label="Rename section"
                    delete-label="Delete section"
                    :rename="(name) => renameSection(section.id, name)"
                    :move-up="() => moveSection(module, si, -1)"
                    :move-down="() => moveSection(module, si, 1)"
                    :remove="() => removeSection(section.id)"
                  />

                  <ul v-if="section.pages.length" class="flex flex-col gap-2 pl-4">
                    <li v-for="(page, pi) in section.pages" :key="page.id">
                      <AdminRow
                        :value="page.title"
                        :can-move-up="pi > 0"
                        :can-move-down="pi < section.pages.length - 1"
                        rename-label="Rename page"
                        delete-label="Delete page"
                        :rename="(title) => renamePage(page.id, title)"
                        :move-up="() => movePage(section, pi, -1)"
                        :move-down="() => movePage(section, pi, 1)"
                        :remove="() => removePage(page.id)"
                      />
                    </li>
                  </ul>

                  <AdminAdd
                    label="New page"
                    placeholder="Page title"
                    button-label="Add page"
                    :add="(title) => addPage(section.id, title)"
                  />
                </div>

                <Separator v-if="module.sections.length" />

                <AdminAdd
                  label="New section"
                  placeholder="Section name"
                  button-label="Add section"
                  :add="(name) => addSection(module.id, name)"
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </template>
    </PageLayout>
  </main>
</template>
