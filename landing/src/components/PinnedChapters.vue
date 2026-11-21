<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// The chapters after the hero, as Apple, Arc and Framer do it (research, 2026-11-21, in the vault:
// Kolmi/investigacion_scroll.md): the scroll is the browser's own and is never taken over, a stage
// stays fixed beside the text (`position: sticky`) while the chapters' sentences scroll past it, and
// when a sentence reaches the middle of the screen it lights up and the stage changes to its
// chapter, whose scene then plays by itself. No snapping, so no jerks and no fight with a trackpad's
// momentum (Jose: the snapping version "da tirones raros"). On a phone, and under reduced motion,
// each chapter is simply its sentence and its picture, one under the other.
const props = defineProps({
  // [{ id, title }], one slot per id with the chapter's picture
  chapters: { type: Array, required: true },
})

const DIM = 0.2 // opacity of a word not lit yet
const WORD_MS = 70 // between two words lighting up

const root = ref(null)
const active = ref(0)
const lit = ref(props.chapters.map(() => 0)) // words lit in each sentence
const stacked = ref(false)
const words = computed(() => props.chapters.map((c) => c.title.split(' ')))
let observer = null
const timers = []

// A sentence lights up word by word, once, the first time it reaches the middle.
function light(i) {
  if (lit.value[i] > 0) return
  let k = 0
  const t = setInterval(() => {
    lit.value[i] = ++k
    if (k >= words.value[i].length) clearInterval(t)
  }, WORD_MS)
  timers.push(t)
}

onMounted(() => {
  stacked.value =
    matchMedia('(max-width: 1023px)').matches || matchMedia('(prefers-reduced-motion: reduce)').matches
  if (stacked.value) {
    lit.value = words.value.map((w) => w.length)
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        const i = Number(e.target.dataset.chapter)
        active.value = i
        light(i)
      }
    },
    { rootMargin: '-45% 0px -45% 0px' },
  )
  root.value.querySelectorAll('[data-chapter]').forEach((el) => observer.observe(el))
})
onBeforeUnmount(() => {
  observer?.disconnect()
  timers.forEach(clearInterval)
})
</script>

<template>
  <div ref="root" class="mx-auto w-[min(100%-2rem,76rem)]">
    <!-- Phone or reduced motion: sentence and picture, one chapter under the other. -->
    <template v-if="stacked">
      <section v-for="c in chapters" :id="c.id" :key="c.id" class="flex flex-col gap-8 py-16">
        <h2 class="text-3xl leading-tight font-semibold tracking-tight text-balance text-fg">{{ c.title }}</h2>
        <slot :name="c.id" />
      </section>
    </template>

    <div v-else class="grid grid-cols-[minmax(0,4fr)_minmax(0,7fr)] gap-16">
      <!-- The sentences, scrolling past as usual. -->
      <div>
        <section
          v-for="(c, i) in chapters"
          :id="c.id"
          :key="c.id"
          :data-chapter="i"
          class="flex min-h-[85svh] items-center"
        >
          <h2 class="text-5xl leading-[1.08] font-semibold tracking-tight text-balance text-fg" :aria-label="c.title">
            <template v-for="(word, k) in words[i]" :key="k"><span class="word" :style="{ opacity: k < lit[i] ? 1 : DIM }" aria-hidden="true">{{ word }}</span>{{ ' ' }}</template>
          </h2>
        </section>
      </div>

      <!-- The stage, fixed beside them: it shows the chapter whose sentence is in the middle. -->
      <div class="relative">
        <div class="sticky top-0 flex h-svh items-center">
          <Transition name="stage" mode="out-in">
            <div :key="chapters[active].id" class="w-full">
              <slot :name="chapters[active].id" />
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.word {
  transition: opacity 300ms ease-out;
}
.stage-enter-active,
.stage-leave-active {
  transition:
    opacity 320ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    filter 320ms ease;
}
.stage-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.98);
  filter: blur(6px);
}
.stage-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
  filter: blur(6px);
}
</style>
