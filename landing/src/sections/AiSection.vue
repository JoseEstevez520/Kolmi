<script setup>
import { BookOpen, Bot, GitBranch, Library, NotebookPen } from '@lucide/vue'
import { CodeBlock, Diagram, DiagramArea, DiagramArrow, DiagramChip, DiagramGroup } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichParas from '../components/RichParas.vue'
import { copy } from '../i18n.js'

// The MCP, told as the case it is for: a member's own AI reads the material (here Moodle and a
// repo) and leaves notes in Kolmi, as that member. One small diagram and the command a coding
// agent runs to connect, as docs/mcp.md has it.
const AI = '#7c3aed'
</script>

<template>
  <LandingSection id="ai" :title="copy.ai.title">
    <RichParas :text="copy.ai.body" />
    <Diagram :label="copy.ai.label">
      <DiagramGroup>
        <DiagramArea :title="copy.ai.material" :icon="Library" layout="row">
          <DiagramChip :icon="BookOpen">{{ copy.ai.moodle }}</DiagramChip>
          <DiagramChip :icon="GitBranch">{{ copy.ai.repo }}</DiagramChip>
        </DiagramArea>
        <DiagramArrow :label="copy.ai.reads" />
        <DiagramChip :icon="Bot" :color="AI">{{ copy.ai.assistant }}</DiagramChip>
        <DiagramArrow :label="copy.ai.leaves" />
        <DiagramChip :icon="NotebookPen">{{ copy.ai.notes }}</DiagramChip>
      </DiagramGroup>
    </Diagram>
    <RichParas :text="copy.ai.connect" />
    <CodeBlock :code="copy.ai.command" language="bash" wrap />
  </LandingSection>
</template>
