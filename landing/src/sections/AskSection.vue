<script setup>
import { ref } from 'vue'
import { NotebookPen } from '@lucide/vue'
import { ChatMessage, ChatProposal } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import RichParas from '../components/RichParas.vue'
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
    <!-- The conversation in a box like the note's on the left, the text on the right (Jose, 2026-11-21). -->
    <div class="grid items-center gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-12">
      <figure class="chat-box m-0 order-2 lg:order-1" :aria-label="copy.ask.label">
        <div class="flex flex-col gap-5">
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
      </figure>
      <RichParas class="order-1 lg:order-2" :text="copy.ask.body" />
    </div>
  </LandingSection>
</template>

<style scoped>
/* The same sheet as the note in the section above: the page's own colour, a soft edge, rounded. */
.chat-box {
  padding: 1.75rem;
  border-radius: 2rem;
  background: var(--color-bg);
  box-shadow: 0 0 0 1px var(--color-border);
}
</style>
