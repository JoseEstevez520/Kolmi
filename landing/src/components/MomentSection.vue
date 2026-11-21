<script setup>
// One moment of the landing: a single sentence, large, and the picture that shows it. No more text
// than that (Jose, 2026-11-21: the old landing "tiene demasiado texto").
defineProps({
  id: { type: String, default: undefined },
  title: { type: String, required: true },
})
</script>

<template>
  <section :id="id" class="scroll-mt-20 py-16 sm:py-24">
    <div class="mx-auto flex w-[min(100%-2rem,64rem)] flex-col items-center gap-10">
      <h2 class="max-w-2xl text-center text-3xl leading-tight font-semibold tracking-tight text-balance text-fg sm:text-4xl">
        {{ title }}
      </h2>
      <div class="w-full"><slot /></div>
    </div>
  </section>
</template>
