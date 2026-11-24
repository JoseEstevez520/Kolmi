<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NodeViewContent, NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { Button } from 'elastic-ui'
import { X } from '@lucide/vue'
import ChatAnswer from './ChatAnswer.vue'
import { AI_LANGUAGE, aiWriting } from '../lib/editor/aiBlock.js'

// A code block of the note editor. Most are code, written as usual. One in the AI's language
// is a piece the AI drew into the note (a diagram, a table): drawn in the page as part of the
// note, not as a chat answer, with a way to remove it on hover. It isn't edited by hand.
const props = defineProps(nodeViewProps)
const { t } = useI18n()

const isAi = computed(() => props.node.attrs.language === AI_LANGUAGE)
</script>

<template>
  <NodeViewWrapper v-if="isAi" class="group relative my-4" contenteditable="false" data-ai-block>
    <ChatAnswer :text="node.textContent" :streaming="Boolean(node.attrs.streaming || aiWriting)" :paced="false" />
    <Button
      v-if="!node.attrs.streaming && !aiWriting && editor.isEditable"
      variant="ghost"
      size="icon"
      :icon="X"
      class="absolute -top-2 -right-2 text-fg-muted opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
      :aria-label="t('notes.ai.remove')"
      :title="t('notes.ai.remove')"
      @click="deleteNode"
    />
    <!-- The program stays in the document (it is what gets saved), out of sight. -->
    <NodeViewContent as="div" class="hidden" />
  </NodeViewWrapper>
  <NodeViewWrapper v-else as="pre">
    <NodeViewContent as="code" :class="node.attrs.language ? `language-${node.attrs.language}` : undefined" />
  </NodeViewWrapper>
</template>
