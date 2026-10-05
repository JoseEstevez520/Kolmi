<script setup>
import { computed } from 'vue'
import { LayoutTemplate, NotebookPen, ShieldCheck } from '@lucide/vue'
import {
  AgentReplay,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// How the pass works, shown as a session rather than boxes and arrows (USAGE 9): a made-up,
// shortened replay of the night that turned the two notes above into the page. AgentReplay
// brings its own aurora, the one that follows the work. Then the README's table, and its
// conclusion in bold.
const ICONS = { gatekeeper: ShieldCheck, notes: NotebookPen, web: LayoutTemplate }

const events = computed(() =>
  copy.value.how.events.map((event) => (event.icon ? { ...event, icon: ICONS[event.icon] } : event)),
)
</script>

<template>
  <LandingSection id="how" :title="copy.how.title">
    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.how.body" /></p>
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.how.lead }}</p>

    <AgentReplay :events="events" :intro="copy.how.intro" />

    <Table :aria-label="copy.how.table.label">
      <TableHeader>
        <TableRow>
          <TableHead v-for="(head, i) in copy.how.table.head" :key="i">{{ head }}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="row in copy.how.table.rows" :key="row[0]">
          <TableCell class="font-medium text-fg">{{ row[0] }}</TableCell>
          <TableCell>{{ row[1] }}</TableCell>
          <TableCell>{{ row[2] }}</TableCell>
        </TableRow>
      </TableBody>
    </Table>

    <p class="text-lg font-semibold text-fg">{{ copy.how.conclusion }}</p>
  </LandingSection>
</template>
