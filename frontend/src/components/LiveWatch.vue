<script setup>
import { nextTick, ref, useTemplateRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Markdown } from 'elastic-ui'
import { ArrowDownToLine, Pause } from '@lucide/vue'

// What a watcher sees of a live note: its text, read-only, following the end while it is
// written. A button stops following so something can be reread, and brings it back.
const props = defineProps({
  content: { type: String, default: '' },
  live: { type: Boolean, default: false },
})

const { t } = useI18n()
const following = ref(true)
const end = useTemplateRef('end')

// Only a note still being written has an end to follow.
async function follow() {
  await nextTick()
  if (following.value && props.live) end.value?.scrollIntoView({ block: 'end', behavior: 'smooth' })
}

watch(() => props.content, follow, { flush: 'post' })
watch(following, follow)
</script>

<template>
  <div>
    <div v-if="live" class="sticky top-[calc(var(--page-header-height)+0.5rem)] z-10 mb-4 flex justify-end">
      <Button
        variant="ghost"
        size="icon"
        :icon="following ? Pause : ArrowDownToLine"
        :aria-pressed="following"
        :aria-label="following ? t('live.stopFollowing') : t('live.followEnd')"
        :title="following ? t('live.stopFollowing') : t('live.followEnd')"
        @click="following = !following"
      />
    </div>
    <Markdown v-if="content.trim()" :source="content" />
    <div ref="end" aria-hidden="true" class="h-px" />
  </div>
</template>
