<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Breadcrumbs } from 'elastic-ui'
import { nodes, trailTo } from '../lib/content.js'

// Where the page sits, at the top: Home, then the sections down to the node, from the tree. The
// chevron after a crumb opens the other nodes at that level, and a crumb whose page changes
// morphs into its new name. The app's own screens are one crumb under Home.
const route = useRoute()
const { t } = useI18n()

const SCREENS = {
  notes: 'sidebar.notes',
  note: 'sidebar.notes',
  settings: 'sidebar.settings',
  admin: 'sidebar.admin',
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
  const screen = SCREENS[route.name]
  return screen ? [home, { label: t(screen), to: route.path }] : [home]
})
</script>

<template>
  <Breadcrumbs :items="items" />
</template>
