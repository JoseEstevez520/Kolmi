<script setup>
import { CalendarDays, Download, Languages, Radio, ScrollText, Users } from '@lucide/vue'
import { Card, CardDescription, CardHeader, CardTitle } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import { copy } from '../i18n.js'

// What else is in the app, as a few small cards with their icon, so the section is scanned
// rather than read. The icons follow the items' order in the locales.
const ICONS = [Radio, CalendarDays, Download, ScrollText, Users, Languages]
</script>

<template>
  <LandingSection id="today" :title="copy.today.title">
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Card v-for="(item, i) in copy.today.items" :key="item.title" size="sm">
        <CardHeader class="gap-3">
          <component :is="ICONS[i]" class="size-5 text-fg-secondary" :stroke-width="1.5" aria-hidden="true" />
          <div class="flex flex-col gap-1">
            <CardTitle size="sm">{{ item.title }}</CardTitle>
            <CardDescription>{{ item.text }}</CardDescription>
          </div>
        </CardHeader>
      </Card>
    </div>
  </LandingSection>
</template>
