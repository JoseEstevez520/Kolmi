<script setup>
import { RouterLink } from 'vue-router'
import { Badge, Card, CardDescription, CardFooter, CardHeader, CardTitle } from 'elastic-ui'

// A card for one item (a note, a link): an optional title and its text, and a
// footer with a short line (a date) and, when it carries meaning, a status
// label with its outcome colour. With a `to` it is a router link, with an
// `href` a plain one; without either it is a plain card.
defineProps({
  to: { type: [String, Object], default: null },
  href: { type: String, default: '' },
  title: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  color: { type: String, default: 'var(--color-fg)' },
  description: { type: String, default: '' },
  meta: { type: String, default: '' },
  status: { type: String, default: '' },
  tone: { type: String, default: '' },
})
</script>

<template>
  <component
    :is="to ? RouterLink : href ? 'a' : 'div'"
    :to="to || undefined"
    :href="href || undefined"
    class="block h-full"
    :class="
      (to || href) &&
      'group rounded-[var(--radius-xl)] focus-visible:outline-2 focus-visible:outline-accent'
    "
  >
    <Card
      size="sm"
      class="h-full"
      :class="(to || href) && 'transition-colors duration-150 group-hover:border-border-strong'"
    >
      <CardHeader class="gap-3">
        <div v-if="icon" class="flex items-start justify-between">
          <component :is="icon" class="size-5 shrink-0" :stroke-width="1.5" :style="{ color }" />
        </div>
        <div class="flex flex-1 flex-col gap-1">
          <CardTitle v-if="title" size="sm">{{ title }}</CardTitle>
          <CardDescription v-if="description" class="leading-relaxed text-fg-secondary">
            {{ description }}
          </CardDescription>
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
