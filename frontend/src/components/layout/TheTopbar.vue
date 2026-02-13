<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
    <div class="text-lg font-semibold text-gray-900">
      <slot name="title" />
    </div>
    <div class="flex items-center gap-4">
      <!-- Health indicator -->
      <div class="flex items-center gap-2 text-sm text-gray-500">
        <span
          class="w-2.5 h-2.5 rounded-full"
          :class="{
            'bg-green-500': appStore.health?.status === 'healthy',
            'bg-red-500': appStore.health && appStore.health.status !== 'healthy',
            'bg-gray-300': !appStore.health,
          }"
        />
        <span>{{ appStore.health?.version ?? '...' }}</span>
      </div>
    </div>
  </header>
</template>
