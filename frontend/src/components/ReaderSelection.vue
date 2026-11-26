<script setup>
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Button,
  Callout,
  Markdown,
  Popover,
  PopoverAnchor,
  PopoverContent,
  SelectionMenu,
  SelectionMenuItem,
  Status,
  TextMorph,
} from 'elastic-ui'
import { ArrowLeft, ArrowRight, MessageSquare, Sparkles, X } from '@lucide/vue'
import { chatEnabled, stageReaderQuestion } from '../lib/chat.js'
import { openChatWide } from '../lib/chatPanel.js'
import { usePacedText } from '../lib/pacedText.js'
import { readingContext, streamReader } from '../lib/reader.js'
import NoteAiFence from './NoteAiFence.vue'

const props = defineProps({
  title: { type: String, default: '' },
  nodeId: { type: Number, default: null },
  liveId: { type: Number, default: null },
  enabled: { type: Boolean, default: null },
  stream: { type: Function, default: streamReader },
})
const active = computed(() => (props.enabled === null ? Boolean(chatEnabled.value) : props.enabled))
const route = useRoute()
const { t } = useI18n()
const host = ref(null)
const selected = ref('')
const context = ref('')
const anchor = shallowRef(null)
const open = ref(false)
const expanded = ref(false)
const glance = ref('')
const detail = ref('')
const glanceComplete = ref(false)
const detailComplete = ref(false)
const working = ref(false)
const streamingText = ref(false)
const error = ref('')
const trail = ref([])
let deeper = null
let controller = null
let run = 0

const { paced: pacedGlance, settling: glanceSettling } = usePacedText(
  () => glance.value,
  () => !expanded.value && streamingText.value,
)
const { paced: pacedDetail, settling: detailSettling } = usePacedText(
  () => detail.value,
  () => expanded.value && streamingText.value,
)

const shownGlance = computed(() => (glanceComplete.value && !glanceSettling.value ? glance.value : pacedGlance.value))
const rawShownDetail = computed(() =>
  detailComplete.value || !streamingText.value ? detail.value : pacedDetail.value,
)
// Keep an unfinished fence out of the reader until its closing fence arrives; completed Artifact
// briefs show their placeholder until the server sends their `fix`.
const drawnDetail = computed(() => rawShownDetail.value.replace(/```kolmi-ai[^\n]*\n(?:(?!```)[\s\S])*$/, ''))
const stepKey = computed(() => `${trail.value.length}:${selected.value}:${expanded.value ? 'detail' : 'glance'}`)

function stop() {
  run++
  controller?.abort()
  controller = null
  working.value = false
  streamingText.value = false
}

function reset() {
  stop()
  trail.value = []
  deeper = null
  open.value = false
  expanded.value = false
  glance.value = ''
  detail.value = ''
  glanceComplete.value = false
  detailComplete.value = false
  error.value = ''
}

function take(text, range) {
  reset()
  selected.value = text
  anchor.value = range
  context.value = readingContext(props.title, host.value?.textContent ?? text, text)
}

async function explain(full = false) {
  stop()
  if (!selected.value || !anchor.value) return
  expanded.value = full
  open.value = true
  error.value = ''
  if (full ? detailComplete.value : glanceComplete.value) return
  if (full) detail.value = ''
  else glance.value = ''
  const request = ++run
  controller = new AbortController()
  working.value = true
  streamingText.value = true
  try {
    await props.stream(selected.value, context.value, {
      detail: full,
      nodeId: props.nodeId,
      liveId: props.liveId,
      history: full && glance.value ? [{ role: 'assistant', text: glance.value }] : [],
      signal: controller.signal,
      onText: (text) => {
        if (request === run) (full ? detail : glance).value = text
      },
      onTextDone: () => {
        if (request === run) streamingText.value = false
      },
    })
    if (request === run) (full ? detailComplete : glanceComplete).value = true
  } catch (e) {
    if (request === run) error.value = e.message || t('reader.failed')
  } finally {
    if (request === run) {
      working.value = false
      streamingText.value = false
    }
  }
}

function stageDeep(text, range) {
  deeper = {
    text,
    range,
    context: readingContext(
      `${props.title} / ${selected.value}`,
      detail.value.replace(/```kolmi-ai[^\n]*\n[\s\S]*?```/g, ''),
      text,
    ),
  }
}

function exploreDeep() {
  if (!deeper || working.value) return
  trail.value.push({
    selected: selected.value,
    context: context.value,
    glance: glance.value,
    detail: detail.value,
    expanded: expanded.value,
    glanceComplete: glanceComplete.value,
    detailComplete: detailComplete.value,
  })
  selected.value = deeper.text
  context.value = deeper.context
  glance.value = ''
  detail.value = ''
  glanceComplete.value = false
  detailComplete.value = false
  error.value = ''
  deeper = null
  explain(false)
}

function back() {
  stop()
  if (!trail.value.length) {
    expanded.value = false
    error.value = ''
    if (!glanceComplete.value) explain(false)
    return
  }
  const previous = trail.value.pop()
  selected.value = previous.selected
  context.value = previous.context
  glance.value = previous.glance
  detail.value = previous.detail
  expanded.value = previous.expanded
  glanceComplete.value = previous.glanceComplete
  detailComplete.value = previous.detailComplete
  error.value = ''
}

function askDeep() {
  if (deeper) {
    stageReaderQuestion(`${props.title} › ${selected.value}`, deeper.text, deeper.context)
    stop()
    open.value = false
    openChatWide()
    return
  }
  ask()
}

function ask() {
  stop()
  open.value = false
  stageReaderQuestion(props.title, selected.value, context.value)
  openChatWide()
}

function retry() {
  if (expanded.value) {
    detail.value = ''
    detailComplete.value = false
  } else {
    glance.value = ''
    glanceComplete.value = false
  }
  explain(expanded.value)
}

watch(active, (value) => {
  if (!value) reset()
})
watch(open, (value) => {
  if (!value) stop()
})
watch(() => route.fullPath, reset)
watch(() => props.nodeId, reset)
watch(() => props.liveId, reset)
onBeforeUnmount(stop)
</script>

<template>
  <div ref="host">
    <SelectionMenu v-if="active" native :label="t('reader.selection')" @select="take">
      <slot />
      <template #actions>
        <SelectionMenuItem
          :icon="Sparkles"
          :aria-label="t('reader.explain')"
          :title="t('reader.explain')"
          @select="explain(false)"
        />
        <SelectionMenuItem
          :icon="MessageSquare"
          :aria-label="t('reader.chat')"
          :title="t('reader.chat')"
          @select="ask"
        />
      </template>
    </SelectionMenu>
    <slot v-else />
  </div>

  <Popover v-model:open="open">
    <PopoverAnchor v-if="anchor" :reference="anchor" />
    <PopoverContent
      side="bottom"
      align="start"
      :side-offset="10"
      fluid
      morph
      :style="{ '--popover-width': expanded ? '38rem' : '24rem' }"
      @open-auto-focus.prevent
      @close-auto-focus.prevent
    >
      <div class="mb-2.5 flex items-center gap-1.5">
        <Button
          v-if="expanded || trail.length"
          variant="ghost"
          size="icon"
          class="size-7 shrink-0"
          :icon="ArrowLeft"
          :aria-label="t('reader.back')"
          :title="t('reader.back')"
          @click="back"
        />
        <span class="min-w-0 flex-1 truncate text-label">
          <span v-if="trail.length" class="text-fg-muted">{{ trail.at(-1).selected }} › </span>
          <TextMorph :text="selected" />
        </span>
        <Button
          variant="ghost"
          size="icon"
          class="size-7 shrink-0"
          :icon="X"
          :aria-label="t('reader.close')"
          :title="t('reader.close')"
          @click="open = false"
        />
      </div>

      <div :key="stepKey" class="curio-step">
        <Callout v-if="error" type="caution">
          <div class="flex items-center justify-between gap-3">
            <span>{{ error }}</span>
            <Button variant="ghost" size="sm" @click="retry">{{ t('reader.retry') }}</Button>
          </div>
        </Callout>

        <Status
          v-if="(working || (expanded ? detailSettling : glanceSettling)) && !(expanded ? drawnDetail : shownGlance)"
          compact
          state="working"
          :label="t('reader.thinking')"
        />

        <SelectionMenu v-if="expanded && drawnDetail" native :label="t('reader.selection')" @select="stageDeep">
          <Markdown :source="drawnDetail" :components="{ 'kolmi-ai': NoteAiFence }" class="curio-prose" />
          <template #actions>
            <SelectionMenuItem
              :icon="Sparkles"
              :disabled="working"
              :aria-label="t('reader.explain')"
              :title="t('reader.explain')"
              @select="exploreDeep"
            />
            <SelectionMenuItem
              :icon="MessageSquare"
              :aria-label="t('reader.chat')"
              :title="t('reader.chat')"
              @select="askDeep"
            />
          </template>
        </SelectionMenu>
        <Markdown v-else-if="!expanded && shownGlance" :source="shownGlance" class="curio-glance text-ui leading-relaxed text-fg-secondary" />

        <div
          v-if="(!expanded && glanceComplete && !working && !glanceSettling) || (expanded && working && !streamingText && drawnDetail)"
          class="mt-3 flex justify-end"
        >
          <Button
            v-if="!expanded && glanceComplete && !working && !glanceSettling"
            variant="ghost"
            size="sm"
            class="text-fg-muted hover:text-fg"
            @click="explain(true)"
          >
            {{ t('reader.explore') }}
            <ArrowRight class="size-3.5" aria-hidden="true" />
          </Button>
          <Status
            v-else-if="expanded && working && !streamingText && drawnDetail"
            compact
            state="working"
            :label="t('reader.building')"
          />
        </div>
      </div>
    </PopoverContent>
  </Popover>
</template>

<style scoped>
.curio-step {
  animation: curio-step-in 200ms var(--ease-soft, ease-out);
}
@keyframes curio-step-in {
  from {
    opacity: 0;
    filter: blur(2px);
  }
}
.curio-glance :deep(p:last-child) {
  margin-bottom: 0;
}
.curio-prose :deep(:first-child) {
  margin-top: 0;
}
.curio-prose :deep(:last-child) {
  margin-bottom: 0;
}
@media (prefers-reduced-motion: reduce) {
  .curio-step {
    animation: none;
  }
}
</style>
