<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// One moment of the landing: a single sentence, large, and the picture that shows it. No more text
// than that (Jose, 2026-11-21: the old landing "tiene demasiado texto").
//
// Layout: the sentence above the picture (`stack`), or beside it (`left`, `right`: the side the
// sentence goes on), so the page does not repeat the same shape (Jose: "no solo texto arriba y
// componente abajo, también texto a los lados"). On a phone it is always stacked.
//
// Motion plays by itself, not with the scroll (Jose: "quiero que vayan solas"): when the moment is
// near the middle of the screen, its sentence lights up word by word and the picture comes up and in, once. Under reduced
// motion all is still.
const props = defineProps({
  id: { type: String, default: undefined },
  title: { type: String, required: true },
  layout: { type: String, default: 'stack' }, // 'stack' | 'left' | 'right'
})

const DIM = 0.2 // opacity of a word not lit yet
const WORD_MS = 90 // time between two words lighting up
const words = computed(() => props.title.split(' '))
const lit = ref(words.value.length)
const shown = ref(true)
const root = ref(null)
let observer = null
let timer = 0

function play() {
  lit.value = 0
  shown.value = true
  timer = setInterval(() => {
    lit.value++
    if (lit.value >= words.value.length) clearInterval(timer)
  }, WORD_MS)
}

onMounted(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
  lit.value = 0
  shown.value = false
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        play()
        observer.disconnect()
      }
    },
    { rootMargin: '-40% 0px -40% 0px' }, // only once it sits near the middle of the screen
  )
  observer.observe(root.value)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  observer?.disconnect()
})

const side = computed(() => props.layout !== 'stack')
</script>

<template>
  <section :id="id" ref="root" class="scroll-mt-20 py-20 sm:py-28">
    <div
      class="mx-auto grid w-[min(100%-2rem,72rem)] items-center gap-10"
      :class="side ? 'lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16' : 'justify-items-center'"
    >
      <h2
        class="text-3xl leading-tight font-semibold tracking-tight text-balance text-fg sm:text-4xl"
        :class="[side ? 'lg:text-5xl' : 'max-w-2xl text-center', layout === 'right' && 'lg:order-2']"
        :aria-label="title"
      >
        <template v-for="(word, i) in words" :key="i"><span class="word" :style="{ opacity: i < lit ? 1 : DIM }" aria-hidden="true">{{ word }}</span>{{ ' ' }}</template>
      </h2>
      <div class="picture w-full" :class="[{ in: shown }, layout === 'right' && 'lg:order-1']"><slot /></div>
    </div>
  </section>
</template>

<style scoped>
.word {
  transition: opacity 300ms ease-out;
}
.picture {
  opacity: 0;
  transform: translateY(18px);
  transition:
    opacity 800ms cubic-bezier(0.22, 1, 0.36, 1) 250ms,
    transform 800ms cubic-bezier(0.22, 1, 0.36, 1) 250ms;
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
