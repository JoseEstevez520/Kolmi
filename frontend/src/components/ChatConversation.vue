<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, ChatMessage, ChatThread, Markdown, StatusText } from 'elastic-ui'
import { profile } from '../lib/auth.js'
import { messages, send, sourceTitles } from '../lib/chat.js'
import { chatSize } from '../lib/chatPanel.js'
import ActionProposal from './ActionProposal.vue'
import ChatAnswer from './ChatAnswer.vue'

// The conversation's messages, drawn once for both places that show it: the floating bubble and
// the full page. The state is the one in lib/chat.js, so both show the same thread.
const { t, tm, rt } = useI18n()

// Before the first question (only the greeting is there) a few ideas to start from, for the
// person's role. Quiet buttons in both sizes; the wide one
// shows four, the small bubble two so it doesn't look cramped.
const full = computed(() => chatSize.value === 'wide')
const empty = computed(() => messages.value.length === 1 && messages.value[0].greeting)
const suggestions = computed(() => {
  const role = profile.value?.role === 'admin' ? 'admin' : 'student'
  const all = tm(`chat.suggestions.${role}`).map((s) => ({ title: rt(s.title), text: rt(s.text) }))
  return all.slice(0, full.value ? 4 : 2)
})
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
        <!-- An answer the backend marks `openui` is an OpenUI Lang program (the chat catalogue),
             drawn as it streams; anything else is Markdown, as before. -->
        <ChatAnswer v-else-if="m.format === 'openui'" :text="m.text" :streaming="Boolean(m.streaming)" />
        <Markdown v-else :source="m.text" />
        <!-- What the assistant wants to change: one card each, decided by the person. -->
        <template v-if="m.proposals?.length" #after>
          <ActionProposal v-for="p in m.proposals" :key="p.id" :proposal="p" />
        </template>
      </ChatMessage>
      <p v-if="m.sources?.length" class="m-0 text-meta text-fg-faint">
        {{ t('chat.sources', { pages: sourceTitles(m.sources) }) }}
      </p>
    </div>
    <div v-if="empty && suggestions.length" class="flex flex-col items-start gap-1">
      <Button
        v-for="s in suggestions"
        :key="s.title"
        variant="ghost"
        size="sm"
        class="h-auto max-w-full justify-start whitespace-normal py-1.5 text-left font-normal text-fg-secondary"
        @click="send(s.text)"
      >
        {{ s.text }}
      </Button>
    </div>
  </ChatThread>
</template>
