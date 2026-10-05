<script setup>
import { ArrowDown, ArrowRight, Check, Database, GitBranch, Hammer, Play, Send, Server } from '@lucide/vue'
import {
  Card,
  CardContent,
  CardFooter,
  Diagram,
  DiagramArea,
  DiagramArrow,
  DiagramChip,
  DiagramGroup,
  Prose,
  Status,
} from 'elastic-ui'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// The README's before-and-after image, made of the app's own parts: the two notes as the Notes
// screen shows them, and the page the nightly pass wrote from them. As the README's image: the
// notes on the left, an arrow, the page on the right. Where the two don't fit side by side (a
// phone, a tablet), it is one column: the notes, an arrow down, the page. The run is real (assets/readme/before-after.*.png); its texts are in the
// locales.
const COLORS = {
  actions: '#7c3aed',
  tests: '#0d9488',
  docker: '#b45309',
  registry: '#2563eb',
  server: '#db2777',
}
</script>

<template>
  <figure class="flex flex-col gap-4" :aria-label="copy.demo.label">
    <div class="grid items-center gap-4 lg:grid-cols-[minmax(0,2fr)_auto_minmax(0,3fr)] lg:gap-6">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
        <Card v-for="(note, i) in copy.demo.notes" :key="i" size="sm">
          <CardContent class="leading-relaxed text-fg-secondary">{{ note }}</CardContent>
          <CardFooter class="mt-auto justify-between gap-3">
            <span class="text-meta text-fg-muted">{{ copy.demo.noteDate }}</span>
            <Status state="done" :label="copy.demo.noteStatus" />
          </CardFooter>
        </Card>
      </div>

      <ArrowDown class="size-5 justify-self-center text-fg-muted lg:hidden" :stroke-width="1.5" aria-hidden="true" />
      <ArrowRight class="hidden size-5 text-fg-muted lg:block" :stroke-width="1.5" aria-hidden="true" />

      <Card>
        <CardContent>
          <Prose>
            <h3>{{ copy.demo.page.title }}</h3>
            <p><RichText :text="copy.demo.page.intro" /></p>
            <Diagram :label="copy.demo.page.diagramLabel">
              <DiagramGroup layout="column">
                <DiagramChip :icon="GitBranch">{{ copy.demo.page.push }}</DiagramChip>
                <DiagramArrow :label="copy.demo.page.triggers" />
                <DiagramArea
                  :title="copy.demo.page.actions"
                  :icon="Play"
                  :color="COLORS.actions"
                  :note="copy.demo.page.actionsNote"
                  layout="row"
                >
                  <DiagramChip :icon="Check" :color="COLORS.tests">{{ copy.demo.page.tests }}</DiagramChip>
                  <DiagramArrow />
                  <DiagramChip :icon="Hammer" :color="COLORS.docker">{{ copy.demo.page.build }}</DiagramChip>
                  <DiagramArrow />
                  <DiagramChip :icon="Send" :color="COLORS.docker">{{ copy.demo.page.pushImage }}</DiagramChip>
                </DiagramArea>
                <DiagramArrow />
                <DiagramChip :icon="Database" :color="COLORS.registry">{{ copy.demo.page.registry }}</DiagramChip>
                <DiagramArrow :label="copy.demo.page.pulls" />
                <DiagramChip :icon="Server" :color="COLORS.server">{{ copy.demo.page.server }}</DiagramChip>
              </DiagramGroup>
            </Diagram>
            <p><strong>{{ copy.demo.page.conclusion }}</strong></p>
          </Prose>
        </CardContent>
      </Card>
    </div>

    <figcaption class="text-center text-sm text-fg-muted">{{ copy.demo.caption }}</figcaption>
  </figure>
</template>
