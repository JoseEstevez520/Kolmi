<script setup>
import { onMounted } from 'vue'
import { Callout, Empty, StatusText } from 'elastic-ui'
import { Home } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { homeNodes, loadNodes, nodesError, nodesLoading } from '../lib/content.js'
import { iconByName } from '../lib/icons.js'

onMounted(() => {
  loadNodes().catch(() => {})
})
</script>

<template>
  <main class="py-16">
    <PageLayout title="Kolmi" lead="Learn as a hive. Everything the class shares, in one place.">
      <StatusText v-if="nodesLoading && homeNodes.length === 0" text="Loading the content…" working />
      <Callout v-else-if="nodesError" type="caution" title="Could not load the content">
        {{ nodesError }}
      </Callout>
      <Empty
        v-else-if="homeNodes.length === 0"
        title="Nothing here yet"
        description="An admin can put a section or a page on the home."
        :icon="Home"
      />
      <CardGrid v-else>
        <PageCard
          v-for="node in homeNodes"
          :key="node.id"
          :title="node.title"
          :description="node.description"
          :icon="iconByName(node.icon)"
          :color="node.color || 'var(--color-fg)'"
          :to="`/node/${node.id}`"
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
