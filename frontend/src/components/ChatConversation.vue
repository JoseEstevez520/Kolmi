<script setup>
import { useI18n } from 'vue-i18n'
import { ChatMessage, ChatProposal, ChatThread, Markdown, StatusText } from 'elastic-ui'
import {
  cancelProposal,
  confirmProposal,
  messages,
  proposalState,
  sourceTitles,
} from '../lib/chat.js'
import { toolIcon, toolLabel } from '../lib/chatTools.js'

// The conversation's messages, drawn once for both places that show it: the floating bubble and
// the full page. The state is the one in lib/chat.js, so both show the same thread.
const { t } = useI18n()
</script>

<template>
  <ChatThread>
    <!-- One child per message (ChatMessage, and the sources line when it has one), so
         ChatThread's "what was just added" glide sees one new thing, not two. -->
    <div v-for="m in messages" :key="m.id" class="flex flex-col gap-1.5">
      <!-- No `text` prop: the answer is Markdown, which ChatStream's plain-text wave can't
           draw, so the default slot takes over for both roles and the "thinking" line is
           drawn here instead of left to ChatMessage. -->
      <ChatMessage :role="m.role">
        <template v-if="m.role === 'user'">{{ m.text }}</template>
        <template v-else-if="m.error">
          <span class="text-[color:var(--color-danger)]">{{ m.error }}</span>
        </template>
        <StatusText v-else-if="!m.text" :text="m.status" working />
        <Markdown v-else :source="m.text" />
        <!-- What the assistant wants to change: one card each, decided by the person. -->
        <template v-if="m.proposals?.length" #after>
          <ChatProposal
            v-for="p in m.proposals"
            :key="p.id"
            :label="toolLabel(p.tool)"
            :icon="toolIcon(p.tool)"
            :args="p.args"
            :state="proposalState(p)"
            v-model:open="p.open"
            :destructive="p.destructive"
            @confirm="(args) => confirmProposal(p, args)"
            @cancel="cancelProposal(p)"
          >
            {{ p.error || p.result }}
          </ChatProposal>
        </template>
      </ChatMessage>
      <p v-if="m.sources?.length" class="m-0 text-meta text-fg-faint">
        {{ t('chat.sources', { pages: sourceTitles(m.sources) }) }}
      </p>
    </div>
  </ChatThread>
</template>
