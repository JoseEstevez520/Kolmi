<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, Status } from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import { api } from '../lib/api.js'
const { t } = useI18n()
const feed = ref(null)
const error = ref('')
onMounted(async () => {
  try { feed.value = await api.notifications() }
  catch (e) { error.value = e.message }
})
</script>
<template>
  <PageLayout :title="t('notifications.title')">
    <Callout v-if="error" type="caution">{{ error }}</Callout>
    <template v-else-if="feed">
      <h2 class="text-title">{{ t('notifications.week') }}</h2>
      <p class="mb-6 text-fg-muted">{{ t('notifications.digest', feed.digest) }}</p>
      <CardGrid>
        <PageCard v-for="item in feed.items" :key="item.id" :to="item.href" :title="item.title || t('notifications.reply')" />
      </CardGrid>
    </template>
    <Status v-else state="working" :label="t('notifications.title')" />
  </PageLayout>
</template>
