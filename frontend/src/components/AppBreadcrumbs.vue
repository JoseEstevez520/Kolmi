<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Breadcrumbs } from 'elastic-ui'
import { nodes, trailTo } from '../lib/content.js'
import { crumbTitle } from '../lib/crumb.js'

// Where the page sits, at the top: Home, then the sections down to the node, from the tree. The
// chevron after a crumb opens the other nodes at that level, and a crumb whose page changes
// morphs into its new name. The app's own screens are one crumb under Home;
// a note is one more, under Notes.
const route = useRoute()
const { t } = useI18n()

const SCREENS = {
  notes: 'sidebar.notes',
  chat: 'chat.page',
  settings: 'sidebar.settings',
  'admin-content': 'sidebar.admin',
  'admin-people': 'sidebar.admin',
  'admin-class': 'sidebar.admin',
  'admin-reports': 'sidebar.admin',
  'admin-log': 'sidebar.aiLog',
}

const crumb = (node) => ({ label: node.title, to: `/node/${node.id}` })

const items = computed(() => {
  const home = { label: t('sidebar.home'), to: '/' }
  if (route.name === 'node') {
    const trail = trailTo(route.params.id, nodes.value).map(({ node, level }) => ({
      ...crumb(node),
      siblings: level.length > 1 ? level.map(crumb) : undefined,
    }))
    return [home, ...trail]
  }
  // A note sits under Notes, named by its title once it has one.
  if (route.name === 'note') {
    return [
      home,
      { label: t('sidebar.notes'), to: '/notes' },
      { label: crumbTitle.value || t('notes.new'), to: route.path },
    ]
  }
  const screen = SCREENS[route.name]
  return screen ? [home, { label: t(screen), to: route.path }] : [home]
})
</script>

<template>
  <Breadcrumbs :items="items" />
</template>
