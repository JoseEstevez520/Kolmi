<script setup>
import { onMounted, ref } from 'vue'
import { copy } from '../i18n.js'

// What Kolmi does, in one loop and without a screen around it: loose notes from several students
// float on the honey (a sticky, a few cards, a photo of the whiteboard), then fly together and turn
// into one page of the class, which stays a moment and goes, and the notes come back. Each note sits
// at a spot of the stage (--l, --t, in container units) and travels to its centre with translate,
// so it works at any width. References: Jose's Pinterest votes of 2026-11-21 (notes floating on a
// coloured background, the note as one big piece). Under reduced motion it shows the page, still.
const reduced = ref(false)
onMounted(() => {
  reduced.value = matchMedia('(prefers-reduced-motion: reduce)').matches
})

// Where each loose note sits, how it leans, and how much later it leaves (seconds).
const SPOTS = [
  { l: '4cqw', t: '10cqh', r: '-6deg', d: 0, kind: 'sticky' },
  { l: '70cqw', t: '6cqh', r: '4deg', d: 0.15, kind: 'card' },
  { l: '8cqw', t: '58cqh', r: '3deg', d: 0.3, kind: 'card' },
  { l: '72cqw', t: '60cqh', r: '-4deg', d: 0.45, kind: 'sticky small' },
]
</script>

<template>
  <figure class="flow m-0" :class="{ still: reduced }" :aria-label="copy.flow.label">
    <div class="stage" aria-hidden="true">
      <div
        v-for="(spot, i) in SPOTS"
        :key="i"
        class="note"
        :class="spot.kind"
        :style="{ '--l': spot.l, '--t': spot.t, '--r': spot.r, '--d': `${spot.d}s` }"
      >
        <div class="bob" :style="{ animationDelay: `${-i * 0.9}s` }">
          <p class="text">{{ copy.flow.notes[i] }}</p>
          <p class="by">{{ copy.flow.by[i] }}</p>
        </div>
      </div>

      <!-- A photo of the whiteboard: four boxes and arrows, drawn by hand. -->
      <div class="note photo" style="--l: 38cqw; --t: 74cqh; --r: -2deg; --d: 0.6s">
        <div class="bob" style="animation-delay: -2.2s">
          <svg viewBox="0 0 220 70" class="sketch">
            <g fill="none" stroke="#2b2b2b" stroke-width="2" stroke-linecap="round">
              <rect x="6" y="20" width="38" height="26" rx="3" />
              <rect x="62" y="20" width="38" height="26" rx="3" />
              <rect x="118" y="20" width="38" height="26" rx="3" />
              <rect x="174" y="20" width="40" height="26" rx="3" />
              <path d="M44 33h16M100 33h16M156 33h16" />
            </g>
            <g font-size="10" fill="#2b2b2b" text-anchor="middle" font-family="ui-rounded, system-ui">
              <text x="25" y="37">{{ copy.flow.sketch[0] }}</text>
              <text x="81" y="37">{{ copy.flow.sketch[1] }}</text>
              <text x="137" y="37">{{ copy.flow.sketch[2] }}</text>
              <text x="194" y="37">{{ copy.flow.sketch[3] }}</text>
            </g>
          </svg>
        </div>
      </div>

      <!-- The page of the class the notes become. -->
      <article class="page">
        <p class="page-title">{{ copy.flow.page.title }}</p>
        <p class="page-line">{{ copy.flow.page.line }}</p>
        <div class="steps">
          <template v-for="(step, i) in copy.flow.page.steps" :key="i">
            <span class="chip" :class="`chip-${i}`">{{ step }}</span>
            <span v-if="i < copy.flow.page.steps.length - 1" class="arrow">→</span>
          </template>
        </div>
        <p class="page-foot">{{ copy.flow.page.foot }}</p>
      </article>
    </div>
  </figure>
</template>

<style scoped>
/* The loop, in seconds: the notes float, gather into the page, the page stays, then goes. */
.flow {
  --loop: 10s;
  width: 100%;
}
.stage {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 1;
  min-height: 22rem;
  container-type: size;
}

.note {
  position: absolute;
  left: var(--l);
  top: var(--t);
  width: min(15rem, 26cqw);
  transform: rotate(var(--r));
  animation: gather var(--loop) cubic-bezier(0.65, 0, 0.35, 1) var(--d) infinite both;
}
.bob {
  padding: 0.9rem 1rem 0.75rem;
  border-radius: 0.9rem;
  background: #fff;
  box-shadow: 0 14px 30px -18px rgb(80 50 0 / 0.45);
  animation: bob 5s ease-in-out infinite;
  text-align: left;
}
.sticky .bob {
  background: #fff3b8;
  border-radius: 0.35rem;
}
.small {
  width: min(12rem, 22cqw);
}
.photo {
  width: min(16rem, 28cqw);
}
.photo .bob {
  padding: 0.5rem;
  background: #f4f4f1;
  border: 6px solid #fff;
}
.sketch {
  display: block;
  width: 100%;
}
.text {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.35;
  color: #3a3a36;
}
.by {
  margin: 0.45rem 0 0;
  font-size: 0.75rem;
  color: #8a867c;
}

/* A note floats, then travels to the centre of the stage shrinking and fading, stays hidden while
   the page shows, and comes back. */
@keyframes gather {
  0%,
  28% {
    transform: translate(0, 0) rotate(var(--r));
    opacity: 1;
  }
  46% {
    transform: translate(calc(50cqw - var(--l) - 50%), calc(50cqh - var(--t) - 50%)) rotate(0deg) scale(0.35);
    opacity: 0;
  }
  47%,
  86% {
    transform: translate(0, 12px) rotate(var(--r)) scale(0.92);
    opacity: 0;
  }
  100% {
    transform: translate(0, 0) rotate(var(--r));
    opacity: 1;
  }
}
@keyframes bob {
  50% {
    translate: 0 -6px;
  }
}

.page {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(34rem, 70cqw);
  padding: 1.5rem 1.6rem 1.25rem;
  border-radius: 1.4rem;
  background: #fff;
  box-shadow: 0 30px 60px -30px rgb(80 50 0 / 0.5);
  text-align: left;
  translate: -50% -50%;
  animation: page var(--loop) cubic-bezier(0.22, 1, 0.36, 1) infinite both;
}
@keyframes page {
  0%,
  42% {
    opacity: 0;
    transform: scale(0.9);
    filter: blur(10px);
  }
  54%,
  84% {
    opacity: 1;
    transform: none;
    filter: none;
  }
  94%,
  100% {
    opacity: 0;
    transform: scale(0.97);
    filter: blur(6px);
  }
}
.page-title {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
  font-weight: 650;
  letter-spacing: -0.01em;
  color: #1a1a18;
}
.page-line {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #4a4842;
}
.steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}
.chip {
  padding: 0.3rem 0.6rem;
  border-radius: 0.55rem;
  font-size: 0.82rem;
  font-weight: 550;
  background: #f1f0ec;
  color: #2d2b27;
}
.chip-1 {
  background: #efe9fe;
  color: #5b3fd6;
}
.chip-2 {
  background: #e7f0ff;
  color: #2563eb;
}
.chip-3 {
  background: #e6f6ec;
  color: #1c7c45;
}
.arrow {
  color: #a19d92;
  font-size: 0.85rem;
}
.page-foot {
  margin: 1rem 0 0;
  font-size: 0.75rem;
  color: #8a867c;
}

/* Reduced motion: the page, still, with the notes around it. */
.still .note,
.still .bob,
.still .page {
  animation: none;
}
.still .page {
  opacity: 1;
}
</style>
