<script setup>
import {
  BookOpen,
  CalendarDays,
  Compass,
  Download,
  FolderTree,
  Languages,
  Map,
  Moon,
  NotebookPen,
  ScrollText,
} from '@lucide/vue'
import { Card, CardDescription, CardHeader, CardTitle } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import { copy } from '../i18n.js'

// What a student and an admin can do, as the README lists it, each as a card with its icon, so
// the section is scanned rather than read. The icons follow the items' order in the locales; on a
// wide screen each role fills its rows (six in threes, four in one).
const ROLES = [
  { key: 'student', icons: [NotebookPen, BookOpen, Compass, CalendarDays, Map, Download], wide: 'lg:grid-cols-3' },
  { key: 'admin', icons: [Moon, ScrollText, FolderTree, Languages], wide: 'lg:grid-cols-4' },
]
</script>

<template>
  <LandingSection id="today" :title="copy.today.title">
    <div v-for="role in ROLES" :key="role.key" class="flex flex-col gap-4">
      <h3 class="text-lg font-semibold text-fg">{{ copy.today[role.key].title }}</h3>
      <div class="grid gap-4 sm:grid-cols-2" :class="role.wide">
        <Card v-for="(item, i) in copy.today[role.key].items" :key="item.title" size="sm">
          <CardHeader class="gap-3">
            <component :is="role.icons[i]" class="size-5 text-fg-secondary" :stroke-width="1.5" aria-hidden="true" />
            <div class="flex flex-col gap-1">
              <CardTitle size="sm">{{ item.title }}</CardTitle>
              <CardDescription>{{ item.text }}</CardDescription>
            </div>
          </CardHeader>
        </Card>
      </div>
    </div>
  </LandingSection>
</template>
