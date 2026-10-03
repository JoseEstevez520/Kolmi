<script setup>
import { NavTreeGroup, NavTreeItem } from 'elastic-ui'

// The content tree as places to pick, inside a NavTree whose value is the picked node's id. A
// section with something in it folds open from its chevron, and its label picks the section
// itself; everything else is a plain item.
defineProps({
  items: { type: Array, required: true },
})
</script>

<template>
  <template v-for="item in items" :key="item.id">
    <NavTreeGroup v-if="item.children?.length" :label="item.title" :value="String(item.id)">
      <PlaceTree :items="item.children" />
    </NavTreeGroup>
    <NavTreeItem v-else :value="String(item.id)">{{ item.title }}</NavTreeItem>
  </template>
</template>
