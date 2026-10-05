<script setup>
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// What a student and an admin can do, as the README lists it.
</script>

<template>
  <LandingSection id="today" :title="copy.today.title">
    <div v-for="role in [copy.today.student, copy.today.admin]" :key="role.title" class="flex flex-col gap-3">
      <h3 class="text-lg font-semibold text-fg">{{ role.title }}</h3>
      <ul class="flex list-disc flex-col gap-2 pl-5 leading-relaxed text-fg-secondary marker:text-fg-faint">
        <li v-for="item in role.items" :key="item"><RichText :text="item" /></li>
      </ul>
    </div>
  </LandingSection>
</template>
