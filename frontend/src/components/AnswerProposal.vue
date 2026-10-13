<script setup>
import { computed } from 'vue'
import { messages } from '../lib/chat.js'
import ActionProposal from './ActionProposal.vue'

// A proposal the answer points at by id: the same card, state and handlers as the ones the
// conversation draws from `m.proposals` (ChatConversation.vue). Nothing is drawn until the
// backend's proposal with that id has arrived.
const props = defineProps({ id: { type: [String, Number], required: true } })
const proposal = computed(() =>
  messages.value.flatMap((m) => m.proposals ?? []).find((p) => String(p.id) === String(props.id)),
)
</script>

<template>
  <ActionProposal v-if="proposal" :proposal="proposal" />
</template>
