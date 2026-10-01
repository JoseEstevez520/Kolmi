<script setup>
// Login and Register: one card centred on the viewport, the hive's mark on top
// and the theme toggle in a corner. Grey, no shadows of our own (elastic-ui
// USAGE 8); the library draws the card, the app only says what is inside.
import { Card, CardContent, CardDescription, CardHeader, CardTitle, ThemeToggle } from 'elastic-ui'
</script>

<template>
  <main class="relative flex min-h-svh flex-col items-center justify-center px-5 py-12">
    <ThemeToggle class="absolute top-4 right-4" />

    <Card class="w-full max-w-[400px]">
      <CardHeader class="items-center gap-3 text-center">
        <img src="/logo.svg" alt="" width="72" height="72" class="size-[72px]" />
        <div class="flex flex-col gap-1">
          <CardTitle as="h1">Kolmi</CardTitle>
          <CardDescription>Learn as a hive.</CardDescription>
        </div>
      </CardHeader>

      <CardContent>
        <slot />
      </CardContent>
    </Card>
  </main>
</template>
