<script setup>
import {
  ChartColumn,
  Clapperboard,
  Code,
  LayoutTemplate,
  ListTree,
  MousePointerClick,
  NotebookPen,
  Table,
  Workflow,
} from '@lucide/vue'
import { Diagram, DiagramArea, DiagramArrow, DiagramChip, DiagramGroup } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import { copy } from '../i18n.js'

// What a page can hold, told as one small diagram rather than a sample of each piece: loose
// notes go in, the web agent lays them out, and the page comes out organized, with the pieces it
// may use. The pieces' icons follow their order in the locales.
const PAGE = '#d97706'
const PIECES = [ListTree, Workflow, ChartColumn, Table, Code, Clapperboard, MousePointerClick]
</script>

<template>
  <LandingSection id="pages" :title="copy.pages.title">
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.pages.lead }}</p>
    <Diagram :label="copy.pages.label">
      <DiagramGroup>
        <DiagramChip :icon="NotebookPen">{{ copy.pages.notes }}</DiagramChip>
        <DiagramArrow :label="copy.pages.agent" />
        <DiagramArea :title="copy.pages.page" :icon="LayoutTemplate" :color="PAGE" layout="row">
          <DiagramChip v-for="(piece, i) in copy.pages.pieces" :key="piece" :icon="PIECES[i]" :color="PAGE">
            {{ piece }}
          </DiagramChip>
        </DiagramArea>
      </DiagramGroup>
    </Diagram>
    <p class="text-lg font-semibold text-fg">{{ copy.pages.conclusion }}</p>
  </LandingSection>
</template>
