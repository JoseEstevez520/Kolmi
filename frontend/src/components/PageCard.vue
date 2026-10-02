<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Card, CardDescription, CardFooter, CardHeader, CardTitle } from 'elastic-ui'
import { ArrowRight, ArrowUpRight } from '@lucide/vue'

// A card for one item (a node, a note): an optional icon, a title and its text,
// and a footer with a short line (a date) and, when it carries meaning, a status
// label with its outcome colour. With a `to` it is a router link, with an `href`
// a plain one; without either it is a plain card. With `clamp`, long text (a
// note) is kept to a few lines with a fading end and a "Show more", so one note
// never dominates the list.
const props = defineProps({
  to: { type: [String, Object], default: null },
  href: { type: String, default: '' },
  title: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  color: { type: String, default: 'var(--color-fg)' },
  description: { type: String, default: '' },
  meta: { type: String, default: '' },
  status: { type: String, default: '' },
  tone: { type: String, default: '' },
  clamp: { type: Boolean, default: false },
})

const { t } = useI18n()

const linked = computed(() => Boolean(props.to || props.href))
const external = computed(() => /^https?:/.test(props.href))

const body = ref(null)
const expanded = ref(false)
const overflowing = ref(false)

async function measure() {
  if (!props.clamp || expanded.value) return
  await nextTick()
  if (body.value) overflowing.value = body.value.scrollHeight > body.value.clientHeight + 1
}

onMounted(measure)
watch(
  () => props.description,
  () => {
    expanded.value = false
    measure()
  },
)
watch(expanded, (open) => {
  if (!open) measure()
})
</script>

<template>
  <component
    :is="to ? RouterLink : href ? 'a' : 'div'"
    :to="to || undefined"
    :href="href || undefined"
    class="block h-full"
    :class="
      linked && 'group rounded-[var(--radius-xl)] focus-visible:outline-2 focus-visible:outline-accent'
    "
  >
    <Card
      size="sm"
      class="h-full"
      :class="linked && 'transition-colors duration-150 group-hover:border-border-strong'"
    >
      <CardHeader class="h-full gap-3">
        <div v-if="icon" class="flex items-start justify-between">
          <component :is="icon" class="size-5 shrink-0" :stroke-width="1.5" :style="{ color }" />
        </div>
        <div class="flex flex-1 flex-col gap-1">
          <CardTitle v-if="title" size="sm" class="flex items-center justify-between gap-2">
            {{ title }}
            <component
              :is="external ? ArrowUpRight : ArrowRight"
              v-if="linked"
              class="size-4 shrink-0 text-fg-faint transition-[color,translate] duration-150 group-hover:text-fg"
              :class="
                external
                  ? 'group-hover:translate-x-0.5 group-hover:-translate-y-0.5'
                  : 'group-hover:translate-x-0.5'
              "
            />
          </CardTitle>

          <template v-if="description">
            <div
              ref="body"
              :class="
                clamp &&
                !expanded && ['max-h-[7rem] overflow-hidden', overflowing && 'mask-fade-note']
              "
            >
              <CardDescription class="leading-relaxed whitespace-pre-line text-fg-secondary">
                {{ description }}
              </CardDescription>
            </div>
            <button
              v-if="clamp && overflowing"
              type="button"
              class="self-start text-xs font-medium text-fg-secondary hover:text-fg focus-visible:outline-2 focus-visible:outline-accent"
              @click="expanded = !expanded"
            >
              {{ expanded ? t('notes.showLess') : t('notes.showMore') }}
            </button>
          </template>
        </div>
      </CardHeader>

      <CardFooter v-if="meta || status" class="mt-auto justify-between gap-3">
        <time v-if="meta" class="text-meta text-fg-muted">{{ meta }}</time>
        <Badge v-if="status" :color="tone || undefined" :class="!meta && 'ml-auto'">
          {{ status }}
        </Badge>
      </CardFooter>
    </Card>
  </component>
</template>
