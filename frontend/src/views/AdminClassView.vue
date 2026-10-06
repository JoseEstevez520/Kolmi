<script setup>
import AdminChat from '../components/AdminChat.vue'
import AdminClassLanguage from '../components/AdminClassLanguage.vue'
import AdminPass from '../components/AdminPass.vue'
import AdminSignups from '../components/AdminSignups.vue'

// The class settings: one of the admin's pages (AdminView holds the title and the selector).
</script>

<template>
  <div class="not-prose flex flex-col divide-y divide-border border-y border-border">
    <AdminClassLanguage />
    <AdminPass />
    <AdminChat />
    <AdminSignups />
  </div>
</template>
