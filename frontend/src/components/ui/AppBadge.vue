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
      'bg-green-100 text-green-800': variant === 'success',
      'bg-yellow-100 text-yellow-800': variant === 'warning',
      'bg-red-100 text-red-800': variant === 'error',
      'bg-blue-100 text-blue-800': variant === 'info',
      'bg-gray-100 text-gray-800': variant === 'neutral' || !variant,
    }"
  >
    {{ text }}
  </span>
</template>
