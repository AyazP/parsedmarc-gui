<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import UpdateBadge from '@/components/updates/UpdateBadge.vue'

const appStore = useAppStore()
</script>

<template>
  <header class="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 flex-shrink-0">
    <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
      <slot name="title" />
    </div>
    <div class="flex items-center gap-3">
      <!-- Update notification -->
      <UpdateBadge />
      <!-- Dark mode toggle -->
      <button
        class="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        @click="appStore.toggleDarkMode()"
        :title="appStore.darkMode ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <!-- Sun icon (shown in dark mode) -->
        <svg v-if="appStore.darkMode" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
        </svg>
        <!-- Moon icon (shown in light mode) -->
        <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
        </svg>
      </button>
      <!-- Health indicator -->
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <span
          class="w-2.5 h-2.5 rounded-full"
          :class="{
            'bg-green-500': appStore.health?.status === 'healthy',
            'bg-red-500': appStore.health && appStore.health.status !== 'healthy',
            'bg-gray-300 dark:bg-gray-600': !appStore.health,
          }"
        />
        <span>{{ appStore.health?.version ?? '...' }}</span>
      </div>
    </div>
  </header>
</template>
