<script setup>
import { ref } from 'vue'
import { NotebookPen } from '@lucide/vue'
import { ChatMessage, ChatProposal } from 'elastic-ui'
import RichText from './RichText.vue'
import { copy } from '../i18n.js'

// The chat, as the app draws it, without the words around it: a question answered from the notes
// with its sources, and a change proposed as a card to confirm. Made up; the card works, with
// nothing behind it.
const state = ref('proposed')

function confirm() {
  state.value = 'working'
  setTimeout(() => (state.value = 'done'), 700)
}
</script>

<template>
  <figure class="m-0 mx-auto flex w-full max-w-2xl flex-col gap-5" :aria-label="copy.ask.label">
    <ChatMessage role="user">{{ copy.ask.question }}</ChatMessage>
    <div class="flex flex-col gap-1.5">
      <ChatMessage role="assistant"><RichText :text="copy.ask.answer" /></ChatMessage>
      <p class="m-0 text-meta text-fg-faint">{{ copy.ask.sources }}</p>
    </div>
    <ChatMessage role="user">{{ copy.ask.request }}</ChatMessage>
    <ChatMessage role="assistant">
      {{ copy.ask.reply }}
      <template #after>
        <ChatProposal
          :label="state === 'done' ? copy.ask.proposal.done : copy.ask.proposal.label"
          :icon="NotebookPen"
          :args="copy.ask.proposal.args"
          :state="state"
          @confirm="confirm"
          @cancel="state = 'cancelled'"
        >
          {{ copy.ask.proposal.result }}
        </ChatProposal>
      </template>
    </ChatMessage>
  </figure>
</template>
