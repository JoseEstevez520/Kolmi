<script setup>
import { computed } from 'vue'
import { ChatProposal } from 'elastic-ui'
import { cancelProposal, confirmProposal, proposalState } from '../lib/chat.js'
import { toolIcon, toolLabel } from '../lib/chatTools.js'
import { previewFor } from './actionPreviews/index.js'

// One proposed change, as the card the person decides on plus, when the tool has one, a picture
// of what it would do. Shared by the streamed answers (AnswerProposal) and the conversation's
// own list (ChatConversation), so both look and act the same.
const props = defineProps({ proposal: { type: Object, required: true } })
const state = computed(() => proposalState(props.proposal))
const preview = computed(() => previewFor(props.proposal.tool))
// Once decided the card itself says what happened; the picture is only for the choosing.
const showPreview = computed(() => preview.value && !['done', 'cancelled'].includes(state.value))
</script>

<template>
  <ChatProposal
    :label="toolLabel(proposal.tool)"
    :icon="toolIcon(proposal.tool)"
    :args="proposal.args"
    :state="state"
    v-model:open="proposal.open"
    :destructive="proposal.destructive"
    :details="preview ? 'edit' : 'always'"
    @confirm="(args) => confirmProposal(proposal, args)"
    @cancel="cancelProposal(proposal)"
  >
    <template v-if="showPreview" #preview>
      <component :is="preview" :tool="proposal.tool" :args="proposal.args" />
    </template>
    {{ proposal.error || proposal.result }}
  </ChatProposal>
</template>
