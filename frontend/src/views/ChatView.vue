<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Aurora, Chat, ChatComposer } from 'elastic-ui'
import ChatConversation from '../components/ChatConversation.vue'
import { activity, greet, responding, send, settled } from '../lib/chat.js'

// The same conversation as the bubble's, full screen: the aurora fills the whole pane and one
// reading width floats over it, the composer at the bottom. Nothing is kept between visits, so a first
// visit here greets just as the bubble does.
const { t } = useI18n()
onMounted(greet)

// The composer and your messages turn to glass over the aurora, as in the bubble (the library
// sets the same tokens there; its helper isn't exported).
const glass = {
  '--chat-composer-bg': 'var(--glass-bg)',
  '--chat-bubble': 'var(--glass-bg)',
  '--chat-composer-shadow': 'drop-shadow(0 2px 6px rgb(0 0 0 / 0.04))',
  '--chat-bubble-shadow': 'var(--glass-shadow)',
  '--chat-bubble-blur': 'var(--glass-blur)',
}
</script>

<template>
  <!-- App.vue hands this page the whole pane (route meta `fullBleed`), header included, so the
       aurora runs edge to edge and the thread starts below the header. -->
  <Aurora :settled="settled" :activity="activity" class="absolute inset-0">
    <Chat :style="glass" class="mx-auto h-full w-full max-w-3xl px-4 pt-14 pb-4">
      <ChatConversation />
      <ChatComposer :placeholder="t('chat.placeholder')" :responding="responding" @send="send" />
    </Chat>
  </Aurora>
</template>
