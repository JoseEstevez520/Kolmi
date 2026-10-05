<script setup>
import { Card, CardDescription, CardHeader, CardTitle } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import { copy } from '../i18n.js'

// The README's documentation and ecosystem lists, each entry a card that is its link
// (USAGE 12): two columns, one on a phone.
</script>

<template>
  <LandingSection v-for="group in [copy.docs, copy.ecosystem]" :key="group.title" :title="group.title">
    <div class="grid gap-4 sm:grid-cols-2">
      <Card v-for="item in group.items" :key="item.href" :href="item.href" size="sm">
        <CardHeader>
          <CardTitle size="sm">{{ item.title }}</CardTitle>
          <CardDescription>{{ item.text }}</CardDescription>
        </CardHeader>
      </Card>
    </div>
  </LandingSection>
</template>
