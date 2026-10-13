<script setup>
import { provide, ref } from 'vue'
import { ChatMessage, ChatProposal, ThemeToggle } from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'
import { previewFor } from '../components/actionPreviews/index.js'
import { toolIcon, toolLabel } from '../lib/chatTools.js'
import { PREVIEW_DATA } from '../lib/previewData.js'

// Development only (/dev/actions): the real action previews (components/actionPreviews) drawn
// with static fake data and no API. The data is provided under the key the previews read their
// data from, so they are the very components the chat uses. Each sits in its card's `preview` slot,
// as in the chat (ActionProposal.vue).

const noop = () => {}
const open = ref(false)

const pageBefore = `# Subnetting

A subnet mask splits an address in two parts.

- /24 gives 254 hosts
- /25 gives 126 hosts

Use the mask to find the network address.
`
const pageAfter = `# Subnetting

A subnet mask splits an address in two parts: network and host.

- /24 gives 254 hosts
- /25 gives 126 hosts
- /26 gives 62 hosts

Use the mask to find the network address.

## Example

192.168.1.77/26 belongs to the network 192.168.1.64.
`

const leaf = (id, title) => ({ id, kind: 'page', title, children: [] })
const tree = [
  {
    id: 12,
    kind: 'section',
    title: 'Unit 1',
    children: [leaf(131, 'Networks'), leaf(132, 'SQL basics'), leaf(134, 'Indexes'), leaf(135, 'Joins'), leaf(136, 'Views')],
  },
  { id: 13, kind: 'section', title: 'Unit 2', children: [leaf(133, 'ORMs'), leaf(137, 'Hibernate'), leaf(138, 'JPA'), leaf(139, 'Spring Data')] },
  { id: 14, kind: 'section', title: 'Extra', children: [leaf(141, 'Docker'), leaf(142, 'Thymeleaf'), leaf(143, 'Git'), leaf(144, 'CI')] },
]

const person = (id, name, role, status, notes) => ({ id, name, role, status, notes, email: `${name.split(' ')[0].toLowerCase()}@example.com` })

const staticData = {
  nodes: ref(tree),
  pages: ref({ 131: { id: 131, content_md: pageBefore } }),
  schedule: ref({
    settings: {
      schedule_days: [1, 2, 3, 4, 5],
      schedule_start: '08:00',
      schedule_end: '13:00',
      schedule_breaks: [],
      schedule_session_minutes: 50,
    },
    events: [
      { id: 1, day: 0, start_time: '08:10', end_time: '09:50', title: 'Databases' },
      { id: 2, day: 1, start_time: '08:10', end_time: '10:40', title: 'Systems' },
      { id: 3, day: 2, start_time: '09:00', end_time: '10:40', title: 'Web' },
    ],
  }),
  users: ref([
    person('7', 'Lucia Prado', 'student', 'pending', 3),
    person('8', 'Mateo Rey', 'student', 'active', 12),
    person('9', 'Ines Vega', 'student', 'pending', 0),
  ]),
  ensure: { nodes: noop, page: noop, schedule: noop, users: noop },
  // The notes list a delete preview counts from.
  loadNotes: async () => [{ node_id: 131 }, { node_id: 131 }, { node_id: 132 }, { node_id: 12 }],
}
provide(PREVIEW_DATA, staticData)

// Mock proposals: the same tool names and args the backend sends.
const cases = [
  {
    title: '1. create_note (student)',
    say: 'I will leave this note for the daily pass.',
    tool: 'create_note',
    args: { content: '> The /26 mask leaves 62 hosts. **Remember** to subtract the network and broadcast addresses.', node_id: 131 },
  },
  {
    title: '2. move_node',
    say: 'Thymeleaf fits better next to the ORMs, so I would move it into Unit 2.',
    tool: 'move_node',
    args: { node_id: 142, parent_id: 13 },
  },
  {
    title: '3a. write_page / replace',
    say: 'I rewrote the page with the /26 case and an example.',
    tool: 'write_page',
    args: { node_id: 131, mode: 'replace', markdown: pageAfter },
  },
  {
    title: '3b. write_page / merge',
    say: 'Two notes add a /26 case. I would merge them into the page.',
    tool: 'write_page',
    args: { node_id: 131, mode: 'merge', markdown: '' },
  },
  {
    title: '4. create_node',
    say: 'The notes cover a topic that has no place yet.',
    tool: 'create_node',
    args: { parent_id: null, kind: 'section', title: 'Security', children: [{ title: 'Firewalls' }, { title: 'TLS' }, { title: 'Hardening' }] },
  },
  {
    title: '4b. create_node (page in a long section)',
    say: 'Subnetting has no page yet.',
    tool: 'create_node',
    args: { parent_id: 13, kind: 'page', title: 'Subnetting' },
  },
  {
    title: '5. create_schedule_event',
    say: 'Networks on Thursday fits between Web and the break.',
    tool: 'create_schedule_event',
    args: { day: 3, start_time: '10:40', end_time: '12:20', title: 'Networks' },
  },
  {
    title: '5b. delete_schedule_event',
    say: 'Systems is no longer taught on Tuesday.',
    tool: 'delete_schedule_event',
    args: { event_id: 2 },
    destructive: true,
  },
  {
    title: '6a. set_status',
    say: 'Lucia is waiting to get in.',
    tool: 'set_status',
    args: { user_id: '7', status: 'active' },
  },
  {
    title: '6a2. set_status (several people)',
    say: 'Three people are waiting to get in.',
    tool: 'set_status',
    args: { user_ids: ['7', '8', '9'], status: 'active' },
  },
  {
    title: '6b. set_role',
    say: 'Mateo could help as an admin.',
    tool: 'set_role',
    args: { user_id: '8', role: 'admin' },
  },
  {
    title: '7a. delete_node (destructive)',
    say: 'Deleting this section removes what is inside.',
    tool: 'delete_node',
    args: { node_id: 12 },
    destructive: true,
  },
  {
    title: '7b. delete_user (destructive)',
    say: 'This account was a duplicate.',
    tool: 'delete_user',
    args: { user_id: '8' },
    destructive: true,
  },
]
</script>

<template>
  <main class="py-10">
    <PageLayout title="Action previews">
      <div class="mb-8 flex items-center gap-3 text-meta text-fg-muted">
        <span>The chat's real previews with static data. Each sits inside its card, as in the chat.</span>
        <ThemeToggle class="ml-auto" />
      </div>

      <div class="flex max-w-xl flex-col gap-12">
        <section v-for="c in cases" :key="c.title" class="flex flex-col gap-2">
          <h2 class="m-0 text-ui font-semibold">{{ c.title }}</h2>
          <ChatMessage role="assistant">
            {{ c.say }}
            <template #after>
              <ChatProposal
                :label="toolLabel(c.tool, c.args, staticData)"
                :icon="toolIcon(c.tool)"
                :args="c.args"
                :details="previewFor(c.tool) ? 'edit' : 'always'"
                state="proposed"
                :destructive="c.destructive"
                @confirm="noop"
                @cancel="noop"
              >
                <template v-if="previewFor(c.tool)" #preview>
                  <component :is="previewFor(c.tool)" :tool="c.tool" :args="c.args" />
                </template>
              </ChatProposal>
            </template>
          </ChatMessage>
        </section>

        <section class="flex flex-col gap-2">
          <h2 class="m-0 text-ui font-semibold">Done: no preview, the card says what happened</h2>
          <ChatMessage role="assistant">
            Done, the note is saved.
            <template #after>
              <ChatProposal v-model:open="open" :label="toolLabel('create_note')" :icon="toolIcon('create_note')" :args="{ content: '...' }" state="done">
                Note 48 saved in Networks / Subnetting.
              </ChatProposal>
            </template>
          </ChatMessage>
        </section>
      </div>
    </PageLayout>
  </main>
</template>
