<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// One moment of the landing: a single sentence, large, and the picture that shows it. No more text
// than that (Jose, 2026-11-21: the old landing "tiene demasiado texto").
//
// Two quiet scroll effects, nothing flashy (Jose, 2026-11-21: "no buscaba nada tan llamativo"; of
// the references he liked the text that lights up word by word, henning-tillmann.de): the sentence
// starts dimmed and its words light up in reading order as it rises through the screen, and the
// picture comes up a little and in once, when it is reached. Under reduced motion all is still.
const props = defineProps({
  id: { type: String, default: undefined },
  title: { type: String, required: true },
})

const DIM = 0.22 // opacity of a word not lit yet
const words = computed(() => props.title.split(' '))
const lit = ref(words.value.length)
const shown = ref(true)
const heading = ref(null)
const picture = ref(null)
let observer = null
let frame = 0

// How much of the sentence is lit: none when its top is at 90% of the screen, all at 45%.
function update() {
  frame = 0
  const el = heading.value
  if (!el) return
  const top = el.getBoundingClientRect().top
  const h = window.innerHeight
  const progress = Math.min(1, Math.max(0, (h * 0.9 - top) / (h * 0.45)))
  lit.value = Math.round(progress * words.value.length)
}
const onScroll = () => {
  if (!frame) frame = requestAnimationFrame(update)
}

onMounted(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
  shown.value = false
  update()
  addEventListener('scroll', onScroll, { passive: true })
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        shown.value = true
        observer.disconnect()
      }
    },
    { rootMargin: '0px 0px -15% 0px' },
  )
  observer.observe(picture.value)
})
onBeforeUnmount(() => {
  removeEventListener('scroll', onScroll)
  cancelAnimationFrame(frame)
  observer?.disconnect()
})
</script>

<template>
  <section :id="id" class="scroll-mt-20 py-16 sm:py-24">
    <div class="mx-auto flex w-[min(100%-2rem,64rem)] flex-col items-center gap-10">
      <h2
        ref="heading"
        class="max-w-2xl text-center text-3xl leading-tight font-semibold tracking-tight text-balance text-fg sm:text-4xl"
        :aria-label="title"
      >
        <template v-for="(word, i) in words" :key="i"><span class="word" :style="{ opacity: i < lit ? 1 : DIM }" aria-hidden="true">{{ word }}</span>{{ ' ' }}</template>
      </h2>
      <div ref="picture" class="picture w-full" :class="{ in: shown }"><slot /></div>
    </div>
  </section>
</template>

<style scoped>
.word {
  transition: opacity 260ms ease-out;
}
.picture {
  opacity: 0;
  transform: translateY(18px);
  transition:
    opacity 700ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 700ms cubic-bezier(0.22, 1, 0.36, 1);
}
.picture.in {
  opacity: 1;
  transform: none;
}
@media (prefers-reduced-motion: reduce) {
  .word,
  .picture {
    transition: none;
  }
}
</style>
