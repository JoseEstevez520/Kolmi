<script setup>
import ChatAnswer from './ChatAnswer.vue'

// A ```kolmi-ai fence of a note, wherever the note is drawn as Markdown (a live note, a closed
// one): a piece the AI drew into it, drawn in the page as part of the note.
defineProps({ code: { type: String, default: '' } })
</script>

<template>
  <div class="not-prose my-4">
    <ChatAnswer :text="code" :paced="false" />
  </div>
</template>
