<script setup>
import { computed } from 'vue'
import { LayoutTemplate, NotebookPen, ShieldCheck, Sparkles } from '@lucide/vue'

// A line of the landing's texts with its `**bold**`, `*italic*` and `code` drawn, and two small
// pieces so a description is not all flat text (Jose, 2026-11-21): `[[Ctrl]]` is a key as a keycap,
// and `[[@sparkles]]` or `[[@shield gatekeeper]]` an icon, alone or with its label, as the app
// shows it. The texts are ours, but they still go in as text, never as HTML.
const props = defineProps({
  text: { type: String, required: true },
})

const ICONS = { sparkles: Sparkles, shield: ShieldCheck, notebook: NotebookPen, layout: LayoutTemplate }

const parts = computed(() =>
  props.text
    .split(/(\[\[[^\]]+\]\]|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/)
    .filter(Boolean)
    .map((part) => {
      if (part.startsWith('[[@')) {
        const [name, ...label] = part.slice(3, -2).split(' ')
        return { tag: 'icon', icon: ICONS[name], text: label.join(' ') }
      }
      if (part.startsWith('[[')) return { tag: 'kbd', text: part.slice(2, -2) }
      if (part.startsWith('**')) return { tag: 'strong', text: part.slice(2, -2) }
      if (part.startsWith('*') && part.length > 2) return { tag: 'em', text: part.slice(1, -1) }
      if (part.startsWith('`')) return { tag: 'code', text: part.slice(1, -1) }
      return { tag: null, text: part }
    }),
)
</script>

<template>
  <template v-for="(part, i) in parts" :key="i">
    <kbd v-if="part.tag === 'kbd'" class="key">{{ part.text }}</kbd>
    <span v-else-if="part.tag === 'icon'" class="chip" :class="{ solo: !part.text }"
      ><component :is="part.icon" class="size-[0.95em]" aria-hidden="true" />{{ part.text }}</span
    >
    <code
      v-else-if="part.tag === 'code'"
      class="rounded-sm bg-bg-muted px-[0.35em] py-[0.15em] font-mono text-[0.875em] text-fg"
    >{{ part.text }}</code>
    <em v-else-if="part.tag === 'em'">{{ part.text }}</em>
    <strong v-else-if="part.tag" class="font-semibold text-fg">{{ part.text }}</strong>
    <template v-else>{{ part.text }}</template>
  </template>
</template>

<style scoped>
/* A key as a keycap: flat, a hairline and a slightly thicker bottom edge, as on a keyboard. */
.key {
  display: inline-block;
  min-width: 1.7em;
  margin: 0 0.1em;
  padding: 0.05em 0.45em 0.1em;
  border: 1px solid var(--color-border);
  border-bottom-width: 2px;
  border-radius: 0.4em;
  background: var(--color-bg);
  font-family: inherit;
  font-size: 0.82em;
  font-weight: 600;
  line-height: 1.5;
  text-align: center;
  color: var(--color-fg);
  vertical-align: baseline;
}
/* An icon, with its label or alone, in the app's honey. Inline-block on the text's baseline, so the
   label sits on the same line as the words around it (Jose: they sat higher). */
.chip {
  display: inline-block;
  margin: 0 0.05em;
  padding: 0.05em 0.5em 0.08em 0.4em;
  border-radius: 999px;
  background: #fdf0cf;
  font-size: 0.9em;
  font-weight: 600;
  line-height: 1.5;
  color: #6b4a0f;
  vertical-align: baseline;
}
.chip svg {
  display: inline-block;
  margin-right: 0.3em;
  vertical-align: -0.12em;
}
.chip.solo {
  padding: 0.05em 0.3em 0.08em;
}
.chip.solo svg {
  margin-right: 0;
}
</style>
