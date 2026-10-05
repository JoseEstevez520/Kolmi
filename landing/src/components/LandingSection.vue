<script setup>
// One section of the landing at the page's one width (elastic-ui USAGE 11): its heading, then
// what it says. More room between sections than inside one, so each reads as a unit.
defineProps({
  id: { type: String, default: undefined },
  title: { type: String, default: '' },
})
</script>

<template>
  <section :id="id" class="scroll-mt-20 py-12 sm:py-16" :aria-labelledby="id && title ? `${id}-title` : undefined">
    <div class="mx-auto flex w-[min(100%-2rem,var(--sticky-header-max-width,64rem))] flex-col gap-6">
      <h2 v-if="title" :id="id ? `${id}-title` : undefined" class="text-2xl font-semibold tracking-tight text-fg sm:text-3xl">
        {{ title }}
      </h2>
      <slot />
    </div>
  </section>
</template>
