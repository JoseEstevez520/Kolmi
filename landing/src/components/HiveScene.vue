<script setup>
import { copy } from '../i18n.js'

// What the night pass does, as a picture that plays by itself (Jose, 2026-11-21: the diagram of the
// first chapter "no me gusta… algo más chulo y visual"): loose notes from four students and a photo
// of the whiteboard float around Kolmi's logo, fly into it one after the other, the hive glows, and
// one page of the class comes out of it. Then the page goes back in, the notes come out again, and
// it loops. Each note sits at a spot (--x, --y, from the centre, in container units of the stage)
// and travels to the centre.
// Under reduced motion it shows the page, still.
const SPOTS = [
  { x: '-30cqw', y: '-28cqh', r: '-6deg', kind: 'sticky' },
  { x: '29cqw', y: '-30cqh', r: '4deg', kind: 'card' },
  { x: '-31cqw', y: '24cqh', r: '3deg', kind: 'card' },
  { x: '30cqw', y: '26cqh', r: '-4deg', kind: 'sticky' },
]
</script>

<template>
  <figure class="hive m-0" :aria-label="copy.hive.label">
    <div class="stage" aria-hidden="true">
      <div
        v-for="(text, i) in copy.hive.notes"
        :key="i"
        class="note"
        :class="SPOTS[i].kind"
        :style="{ '--x': SPOTS[i].x, '--y': SPOTS[i].y, '--r': SPOTS[i].r, '--d': `${i * 0.18}s` }"
      >
        <p class="m-0">{{ text }}</p>
        <p class="by">{{ copy.hive.by[i] }}</p>
      </div>
      <div class="note photo" style="--x: 0cqw; --y: 36cqh; --r: -2deg; --d: 0.72s">
        <svg viewBox="0 0 220 56" class="block w-full">
          <g fill="none" stroke="#2b2b2b" stroke-width="2" stroke-linecap="round">
            <rect x="6" y="14" width="38" height="26" rx="3" /><rect x="62" y="14" width="38" height="26" rx="3" />
            <rect x="118" y="14" width="38" height="26" rx="3" /><rect x="174" y="14" width="40" height="26" rx="3" />
            <path d="M44 27h16M100 27h16M156 27h16" />
          </g>
          <g font-size="10" fill="#2b2b2b" text-anchor="middle" font-family="ui-rounded, system-ui">
            <text v-for="(w, i) in copy.hive.sketch" :key="i" :x="25 + i * 56" y="31">{{ w }}</text>
          </g>
        </svg>
      </div>

      <!-- The hive: Kolmi's logo, glowing when the notes go in. -->
      <div class="logo"><img src="/logo.svg" alt="" /></div>

      <!-- The page the notes become. -->
      <article class="page">
        <p class="page-title">{{ copy.hive.page.title }}</p>
        <p class="page-line">{{ copy.hive.page.line }}</p>
        <div class="steps">
          <template v-for="(step, i) in copy.hive.page.steps" :key="i">
            <span class="chip" :class="`chip-${i}`">{{ step }}</span>
            <span v-if="i < copy.hive.page.steps.length - 1" class="arrow">→</span>
          </template>
        </div>
        <p class="page-foot">{{ copy.hive.page.foot }}</p>
      </article>
    </div>
  </figure>
</template>

<style scoped>
.hive {
  --loop: 9s;
}
.stage {
  position: relative;
  container-type: size;
  width: 100%;
  height: clamp(24rem, 58vh, 32rem);
}
.note {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(14rem, 30cqw);
  padding: 0.8rem 0.95rem 0.7rem;
  border-radius: 0.9rem;
  background: #fff;
  box-shadow: 0 14px 30px -18px rgb(80 50 0 / 0.4);
  font-size: 0.9rem;
  line-height: 1.35;
  color: #3a3a36;
  text-align: left;
  animation: into var(--loop) cubic-bezier(0.65, 0, 0.35, 1) var(--d) infinite both;
}
.note.sticky {
  background: #fff3b8;
  border-radius: 0.35rem;
}
.note.photo {
  width: min(15rem, 32cqw);
  padding: 0.45rem;
  border: 5px solid #fff;
  background: #f4f4f1;
}
.by {
  margin: 0.4rem 0 0;
  font-size: 0.72rem;
  color: #8a867c;
}
/* A note shows at its spot, floats, then flies into the hive and stays hidden while the page shows. */
@keyframes into {
  0% {
    opacity: 0;
    transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y) + 12px)) rotate(var(--r)) scale(0.95);
  }
  8%,
  30% {
    opacity: 1;
    transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) rotate(var(--r));
  }
  42% {
    opacity: 0;
    transform: translate(-50%, -50%) rotate(0deg) scale(0.2);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.2);
  }
}

.logo {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 4.5rem;
  height: 4.5rem;
  display: grid;
  place-items: center;
  border-radius: 999px;
  transform: translate(-50%, -50%);
  animation: hive var(--loop) cubic-bezier(0.22, 1, 0.36, 1) infinite both;
}
.logo img {
  width: 3.4rem;
}
@keyframes hive {
  0%,
  30% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgb(240 170 60 / 0);
    transform: translate(-50%, -50%) scale(1);
  }
  44% {
    box-shadow: 0 0 0 1.2rem rgb(240 170 60 / 0.18), 0 0 3rem 1rem rgb(240 170 60 / 0.35);
    transform: translate(-50%, -50%) scale(1.18);
  }
  52%,
  90% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.6);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.page {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(32rem, 94%);
  padding: 1.5rem 1.6rem 1.25rem;
  border-radius: 1.4rem;
  background: #fff;
  box-shadow: 0 30px 60px -30px rgb(80 50 0 / 0.45);
  text-align: left;
  animation: out var(--loop) cubic-bezier(0.22, 1, 0.36, 1) infinite both;
}
@keyframes out {
  0%,
  46% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.3);
    filter: blur(10px);
  }
  58%,
  88% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
    filter: none;
  }
  97%,
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.3);
    filter: blur(8px);
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
.page-foot {
  margin: 1rem 0 0;
  font-size: 0.75rem;
  color: #8a867c;
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

@media (prefers-reduced-motion: reduce) {
  .note,
  .logo {
    display: none;
  }
  .page {
    animation: none;
    transform: translate(-50%, -50%);
  }
}
</style>
