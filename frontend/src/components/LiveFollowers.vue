<script setup>
import { Avatar, AvatarGroup } from 'elastic-ui'

// Who is following a live note: their initials stacked, each name on hover and for screen
// readers. Nobody following draws nothing: no text, no count.
defineProps({ followers: { type: Array, default: () => [] } })
</script>

<template>
  <AvatarGroup v-if="followers.length" size="sm" initials :max="5">
    <Avatar v-for="person in followers" :key="person.id" :name="person.name" />
  </AvatarGroup>
</template>
