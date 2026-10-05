<script setup>
import { Brain, Check, CircleHelp, X } from '@lucide/vue'
import {
  Callout,
  Chart,
  CodeBlock,
  Diagram,
  DiagramArea,
  DiagramChip,
  DiagramGroup,
  DiagramItem,
} from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// What a page can hold, in place of the README's screenshots: the same pieces, live. Each one
// after the sentence that calls for it and before the line that says what it showed (USAGE 9).
// The content is the class's own pages', the ones the screenshots were taken from.
const MODEL = '#7c3aed'
const AGENT = '#0891b2'
const OUTCOME = {
  yes: { icon: Check, color: 'var(--color-success)' },
  asks: { icon: CircleHelp, color: 'var(--color-warning)' },
  no: { icon: X, color: 'var(--color-danger)' },
}

// Who may do what, as the class page draws it.
const AGENTS = [
  { name: 'builder', can: [['edits', 'yes'], ['runs', 'yes']] },
  { name: 'planner', can: [['edits', 'asks'], ['runs', 'asks']] },
  { name: 'tutor', can: [['edits', 'no'], ['runs', 'no']] },
  { name: 'explorer', can: [['reads', 'yes'], ['edits', 'no']] },
]

// Read off the class page's chart (AgentMarketCap, April 2026): cost per solved task in US
// dollars, and the SWE-bench Verified score.
const MODELS = [
  { x: 0.2, y: 79.3, label: 'DeepSeek V4 Pro' },
  { x: 0.45, y: 80.2, label: 'Qwen3.5' },
  { x: 1.4, y: 80.6, label: 'MiniMax M2.5' },
  { x: 11, y: 80.8, label: 'Gemini 3.1 Pro' },
  { x: 17, y: 80.6, label: 'GPT-5.4' },
  { x: 74, y: 80.8, label: 'Claude Opus 4.6' },
]

const WORKFLOW = `on: push

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: <test command>

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t <registry>/<image>:<tag> .
      - run: docker push <registry>/<image>:<tag>
`
</script>

<template>
  <LandingSection id="pages" :title="copy.pages.title">
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.pages.lead }}</p>

    <h3 class="pt-4 text-lg font-semibold text-fg">{{ copy.pages.diagram.title }}</h3>
    <Diagram :label="copy.pages.diagram.label">
      <DiagramGroup layout="column">
        <DiagramChip :icon="Brain" :color="MODEL">{{ copy.pages.diagram.model }}</DiagramChip>
        <DiagramGroup layout="grid">
          <DiagramArea
            v-for="agent in AGENTS"
            :key="agent.name"
            :title="copy.pages.diagram[agent.name]"
            :note="copy.pages.diagram[`${agent.name}Note`]"
            :color="AGENT"
          >
            <DiagramItem
              v-for="[action, answer] in agent.can"
              :key="action"
              :icon="OUTCOME[answer].icon"
              :color="OUTCOME[answer].color"
            >
              {{ copy.pages.diagram[action] }}: {{ copy.pages.diagram[answer] }}
            </DiagramItem>
          </DiagramArea>
        </DiagramGroup>
      </DiagramGroup>
    </Diagram>
    <p class="font-semibold text-fg">{{ copy.pages.diagram.conclusion }}</p>

    <h3 class="pt-4 text-lg font-semibold text-fg">{{ copy.pages.chart.title }}</h3>
    <Chart
      variant="points"
      :series="[{ name: copy.pages.chart.series, points: MODELS }]"
      :x="{ title: copy.pages.chart.x, unit: 'USD', scale: 'log' }"
      :y="{ title: copy.pages.chart.y, unit: '%', min: 79, max: 81 }"
      :label="copy.pages.chart.label"
      :caption="copy.pages.chart.caption"
    />
    <p class="font-semibold text-fg">{{ copy.pages.chart.conclusion }}</p>

    <h3 class="pt-4 text-lg font-semibold text-fg">{{ copy.pages.code.title }}</h3>
    <p class="leading-relaxed text-fg-secondary"><RichText :text="copy.pages.code.lead" /></p>
    <CodeBlock :code="WORKFLOW" title=".github/workflows/ci-cd.yml" />
    <p class="leading-relaxed text-fg-secondary"><RichText :text="copy.pages.code.after" /></p>
    <Callout type="warning"><RichText :text="copy.pages.code.warning" /></Callout>
  </LandingSection>
</template>
