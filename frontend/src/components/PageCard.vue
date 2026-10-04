<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, Card, CardDescription, CardFooter, CardHeader, CardTitle, FileIcon, FolderIcon, Status } from 'elastic-ui'
import { ArrowRight, ArrowUpRight } from '@lucide/vue'

// A card for one item (a node, a note): an optional icon, a title and its text,
// and a footer with a short line (a date) and, when it carries meaning, a Status
// (its `state`, with `status` as the label in the app's own words). With a `to` it is a router link, with an `href`
// a plain one; without either it is a plain card. With `clamp`, long text (a
// note) is kept to a few lines with a fading end and a "Show more", so one note
// never dominates the list; a linked card opens instead of a "Show more".
const props = defineProps({
  to: { type: [String, Object], default: null },
  href: { type: String, default: '' },
  title: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  color: { type: String, default: 'var(--color-fg)' },
  // With no icon, a node's card shows what it is: a folder (section) or a page.
  kind: { type: String, default: '' },
  description: { type: String, default: '' },
  meta: { type: String, default: '' },
  status: { type: String, default: '' },
  state: { type: String, default: '' },
  clamp: { type: Boolean, default: false },
})

const { t } = useI18n()

// The neutral grey unless the node has a colour of its own.
const markColor = computed(() => (props.color === 'var(--color-fg)' ? undefined : props.color))

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
        <div v-if="icon || kind" class="flex items-start justify-between" :class="!icon && 'h-10 items-center'">
          <component :is="icon" v-if="icon" class="size-5 shrink-0" :stroke-width="1.5" :style="{ color }" />
          <FolderIcon v-else-if="kind === 'section'" :color="markColor" />
          <FileIcon v-else name="" :color="markColor" />
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
            <Button
              v-if="clamp && overflowing && !linked"
              variant="link"
              size="sm"
              class="self-start"
              @click="expanded = !expanded"
            >
              {{ expanded ? t('notes.showLess') : t('notes.showMore') }}
            </Button>
          </template>
        </div>
      </CardHeader>

      <CardFooter v-if="meta || state" class="mt-auto justify-between gap-3">
        <time v-if="meta" class="text-meta text-fg-muted">{{ meta }}</time>
        <Status v-if="state" :state="state" :label="status || undefined" :class="!meta && 'ml-auto'" />
      </CardFooter>
    </Card>
  </component>
</template>
