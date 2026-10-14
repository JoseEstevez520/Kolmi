<script setup>
import { Button, Status, ThemeToggle } from 'elastic-ui'
import { ArrowLeft, Paperclip, Radio, Maximize2 } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import LiveFollowers from '../components/LiveFollowers.vue'
import LiveWatch from '../components/LiveWatch.vue'
import PageCard from '../components/PageCard.vue'

// Development only (/dev/live): live notes with the real parts and invented people, no API. It
// shows how a live note reads for who watches, for who writes, and as the first row on Notes.
const followers = [
  { id: '1', name: 'Lucía Prado' },
  { id: '2', name: 'Mateo Rey' },
  { id: '3', name: 'Inés Vega' },
  { id: '4', name: 'Sara Ben' },
  { id: '5', name: 'Hugo Paz' },
  { id: '6', name: 'Noa Gil' },
  { id: '7', name: 'Leo Cruz' },
]
const text = `# Networks: subnetting

A mask splits an address in two parts, network and host.

- /24 gives 254 hosts
- /25 gives 126 hosts
- /26 gives 62 hosts

Next: VLSM, one mask per subnet.`
</script>

<template>
  <main class="mx-auto flex max-w-2xl flex-col gap-16 px-4 py-10">
    <div class="flex items-center text-meta text-fg-muted">
      The live notes with the real parts and invented people.
      <ThemeToggle class="ml-auto" />
    </div>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">1. Notes: the first row, when someone writes live</h2>
      <CardGrid>
        <PageCard to="#" title="Networks: subnetting" description="Next: VLSM, one mask per subnet." meta="Lucía Prado" state="working" status="Live" />
        <PageCard to="#" title="Databases" description="A join combines rows of two tables on a key." meta="Mateo Rey" state="working" status="Live" />
      </CardGrid>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">2. Who watches: the note, with who follows</h2>
      <div class="rounded-xl bg-bg-muted p-6">
        <div class="mb-4 flex items-center justify-between gap-3">
          <Button variant="ghost" size="icon" :icon="ArrowLeft" aria-label="Back" />
          <div class="flex items-center gap-3">
            <LiveFollowers :followers="followers" />
            <Status compact state="working" label="Live" />
          </div>
        </div>
        <h1 class="mb-1 text-display font-semibold">Networks: subnetting</h1>
        <p class="mb-6 text-label text-fg-muted">Lucía Prado</p>
        <LiveWatch :content="text" :live="false" />
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">3. Who writes: the bar over the note, live on, three following</h2>
      <div class="rounded-xl bg-bg-muted p-6">
        <div class="mb-8 flex items-center justify-between gap-3">
          <Button variant="ghost" size="sm" :icon="ArrowLeft">Notes</Button>
          <div class="flex items-center gap-2">
            <LiveFollowers :followers="followers.slice(0, 3)" />
            <Button variant="ghost" size="sm" :icon="Paperclip" class="text-fg-muted">Attach</Button>
            <Button variant="ghost" size="icon" :icon="Radio" class="bg-bg-muted text-fg" aria-pressed="true" aria-label="Share live" />
            <Button variant="ghost" size="icon" :icon="Maximize2" aria-label="Zen mode" />
          </div>
        </div>
        <h1 class="mb-1 text-display font-semibold">Networks: subnetting</h1>
        <div class="text-copy text-fg-secondary">A mask splits an address in two parts, network and host.</div>
      </div>
    </section>
  </main>
</template>
