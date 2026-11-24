<script setup>
import { computed, ref, watch } from 'vue'
import { Markdown } from 'elastic-ui'
import { loadChatRenderer } from '../lib/openui/load-chat.js'
import { usePacedText } from '../lib/pacedText.js'

// A chat answer written in OpenUI Lang and drawn with the chat catalogue. `text` is the raw
// text so far; while `streaming` it is drawn as it arrives, and once the stream ends an answer
// that did not parse (or has no Answer root) is shown as Markdown, so nothing is lost.
const props = defineProps({
  text: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
  paced: { type: Boolean, default: true },
})

// Drawn at the library's steady pace, not in the model's bursts: the same as a chat's plain text.
// A note's editor already paces the stream, so it passes `paced: false` to draw the text as it is.
const { paced: pacedText, settling } = usePacedText(
  () => (props.paced ? props.text : ''),
  () => props.paced && props.streaming,
)
const drawn = computed(() => (props.paced ? pacedText.value : props.text))
const isStreaming = computed(() => props.streaming || (props.paced && settling.value))

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
    v-else-if="openui && drawn"
    :response="drawn"
    :library="openui.chatLibrary"
    :is-streaming="isStreaming"
    :on-error="onError"
  />
</template>
