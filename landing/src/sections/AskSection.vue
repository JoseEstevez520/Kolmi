<script setup>
import { ref } from 'vue'
import { NotebookPen } from '@lucide/vue'
import { ChatMessage, ChatProposal } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// The chat, shown as the app draws it: a question answered from the notes with its sources, and
// a change the chat proposes as a card to confirm (elastic-ui's ChatProposal, the same part the
// app uses), on the page's own background as the app draws it. The conversation is made up, and the card works: Confirm and Cancel move it
// through its states, with nothing behind it.
const state = ref('proposed')

function confirm() {
  state.value = 'working'
  setTimeout(() => (state.value = 'done'), 700)
}
</script>

<template>
  <LandingSection id="chat" :title="copy.ask.title">
    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.ask.body" /></p>

    <figure class="flex flex-col gap-4" :aria-label="copy.ask.label">
      <div class="mx-auto flex w-full max-w-2xl flex-col gap-5">
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
      </div>
      <figcaption class="text-center text-sm text-fg-muted">{{ copy.ask.caption }}</figcaption>
    </figure>

    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.ask.acts }}</p>
  </LandingSection>
</template>
