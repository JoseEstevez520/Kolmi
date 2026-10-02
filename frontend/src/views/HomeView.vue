<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, Empty, StatusText } from 'elastic-ui'
import { Home } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { homeNodes, loadNodes, nodesError, nodesLoading } from '../lib/content.js'
import { iconByName } from '../lib/icons.js'

const { t } = useI18n()

onMounted(() => {
  loadNodes().catch(() => {})
})
</script>

<template>
  <main class="py-16">
    <PageLayout title="Kolmi" :lead="t('home.lead')">
      <StatusText v-if="nodesLoading && homeNodes.length === 0" :text="t('common.loadingContent')" working />
      <Callout v-else-if="nodesError" type="caution" :title="t('common.contentError')">
        {{ nodesError }}
      </Callout>
      <Empty
        v-else-if="homeNodes.length === 0"
        :title="t('common.nothingHere')"
        :description="t('home.empty')"
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
