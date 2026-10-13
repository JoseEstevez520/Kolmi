<script setup>
import { computed, ref, watch } from 'vue'
import { ChatProposal } from 'elastic-ui'
import { cancelProposal, confirmProposal, proposalState } from '../lib/chat.js'
import { prepareLabel, toolIcon, toolLabel } from '../lib/chatTools.js'
import { usePreviewData } from '../lib/previewData.js'
import { previewFor } from './actionPreviews/index.js'

// One proposed change, as the card the person decides on plus, when the tool has one, a picture
// of what it would do. Shared by the streamed answers (AnswerProposal) and the conversation's
// own list (ChatConversation), so both look and act the same.
const props = defineProps({ proposal: { type: Object, required: true } })
const state = computed(() => proposalState(props.proposal))
const data = usePreviewData()
prepareLabel(props.proposal.tool, data)
// The title names what it touches (a page, a person) once the tree or the people are known.
const label = computed(() => toolLabel(props.proposal.tool, props.proposal.args, data))
// The preview follows what the person types in Edit, not just what the model proposed.
const liveArgs = ref(props.proposal.args)
watch(() => props.proposal.args, (args) => (liveArgs.value = args))
const preview = computed(() => previewFor(props.proposal.tool))
// Once decided the card itself says what happened; the picture is only for the choosing.
const showPreview = computed(() => preview.value && !['done', 'cancelled'].includes(state.value))
</script>

<template>
  <ChatProposal
    :label="label"
    :icon="toolIcon(proposal.tool)"
    :args="proposal.args"
    :state="state"
    v-model:open="proposal.open"
    :destructive="proposal.destructive"
    :details="preview ? 'edit' : 'always'"
    @change="(args) => (liveArgs = args)"
    @confirm="(args) => confirmProposal(proposal, args)"
    @cancel="cancelProposal(proposal)"
  >
    <template v-if="showPreview" #preview>
      <component :is="preview" :tool="proposal.tool" :args="liveArgs" />
    </template>
    {{ proposal.error || proposal.result }}
  </ChatProposal>
</template>
