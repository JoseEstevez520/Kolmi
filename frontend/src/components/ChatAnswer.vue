<script setup>
import { computed, ref, watch } from 'vue'
import { Markdown } from 'elastic-ui'
import { loadChatRenderer } from '../lib/openui/load-chat.js'

// A chat answer written in OpenUI Lang and drawn with the chat catalogue. `text` is the raw
// text so far; while `streaming` it is drawn as it arrives, and once the stream ends an answer
// that did not parse (or has no Answer root) is shown as Markdown, so nothing is lost.
const props = defineProps({
  text: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
})

const openui = ref(null)
const failed = ref(false)
const parseFailed = ref(false)

loadChatRenderer()
  .then((loaded) => (openui.value = loaded))
  .catch(() => (failed.value = true))

function onError(errors) {
  if (errors.some((e) => e.code === 'parse-failed' || e.code === 'parse-exception')) {
    parseFailed.value = true
  }
}

// A new text starts clean; the verdict is only read when the stream has ended.
watch(
  () => props.text,
  (now, before) => {
    if (!now || (before && !now.startsWith(before.slice(0, 20)))) parseFailed.value = false
  },
)

const hasRoot = computed(() => (openui.value ? openui.value.canRender(props.text) : true))
const asMarkdown = computed(
  () => !props.streaming && Boolean(props.text) && (failed.value || parseFailed.value || !hasRoot.value),
)
</script>

<template>
  <Markdown v-if="asMarkdown" :source="text" />
  <component
    :is="openui.Renderer"
    v-else-if="openui && text"
    :response="text"
    :library="openui.chatLibrary"
    :is-streaming="streaming"
    :on-error="onError"
  />
</template>
