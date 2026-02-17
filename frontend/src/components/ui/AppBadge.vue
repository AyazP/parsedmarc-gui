<script setup lang="ts">
defineProps<{
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral'
  text: string
}>()
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
    :class="{
      'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400': variant === 'success',
      'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400': variant === 'warning',
      'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400': variant === 'error',
      'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400': variant === 'info',
      'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300': variant === 'neutral' || !variant,
    }"
  >
    {{ text }}
  </span>
</template>
