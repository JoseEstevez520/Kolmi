<script setup>
import { ref } from 'vue'
import { DayStrip, WeekPillbox } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy, locale } from '../i18n.js'

// What a student and an admin can do, as the README lists it. The admin's list ends with the
// one thing to play with on this screen: the controls the admin sets the pass's schedule with.
const days = ref([1, 2, 3, 4, 5])
const times = ref(['03:00'])
</script>

<template>
  <LandingSection id="today" :title="copy.today.title">
    <div v-for="role in [copy.today.student, copy.today.admin]" :key="role.title" class="flex flex-col gap-3">
      <h3 class="text-lg font-semibold text-fg">{{ role.title }}</h3>
      <ul class="flex list-disc flex-col gap-2 pl-5 leading-relaxed text-fg-secondary marker:text-fg-faint">
        <li v-for="item in role.items" :key="item"><RichText :text="item" /></li>
      </ul>
    </div>

    <div class="flex flex-col gap-4">
      <p class="leading-relaxed text-fg-secondary">{{ copy.today.schedule.lead }}</p>
      <WeekPillbox
        v-model="days"
        :locale="locale"
        :label="copy.today.schedule.days"
        :words="copy.today.schedule.words"
        class="self-start"
      />
      <DayStrip v-model="times" :label="copy.today.schedule.times" :add-label="copy.today.schedule.addTime" />
    </div>
  </LandingSection>
</template>
