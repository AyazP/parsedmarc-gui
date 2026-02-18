<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
if (!appStore.initialized) {
  appStore.initialize()
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center p-4">
    <div class="w-full max-w-4xl">
      <!-- Brand header -->
      <div class="flex items-center justify-center gap-3 mb-8">
        <div class="w-10 h-10 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold text-lg">P</div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">ParseDMARC</h1>
      </div>
      <slot />
    </div>
  </div>
</template>
