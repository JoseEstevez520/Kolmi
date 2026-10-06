<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Chat, ChatComposer } from 'elastic-ui'
import ChatConversation from '../components/ChatConversation.vue'
import { greet, responding, send } from '../lib/chat.js'

// The same conversation as the bubble's, full screen: one reading width, the composer at the
// bottom. Nothing is kept between visits, so a first visit here greets just as the bubble does.
const { t } = useI18n()
onMounted(greet)
</script>

<template>
  <Chat class="mx-auto h-[calc(100dvh-8.5rem)] w-full max-w-3xl px-4">
    <ChatConversation />
    <ChatComposer :placeholder="t('chat.placeholder')" :responding="responding" @send="send" />
  </Chat>
</template>
