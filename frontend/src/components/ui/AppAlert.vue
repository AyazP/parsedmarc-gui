<script setup lang="ts">
defineProps<{
  type?: 'info' | 'success' | 'warning' | 'error'
  title?: string
  message?: string
  dismissible?: boolean
}>()

defineEmits<{
  dismiss: []
}>()
</script>

<template>
  <div
    class="rounded-lg p-4"
    :class="{
      'bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400 border border-blue-200 dark:border-blue-800': type === 'info' || !type,
      'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-400 border border-green-200 dark:border-green-800': type === 'success',
      'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800': type === 'warning',
      'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-400 border border-red-200 dark:border-red-800': type === 'error',
    }"
  >
    <div class="flex">
      <div class="flex-1">
        <p v-if="title" class="text-sm font-medium">{{ title }}</p>
        <p v-if="message" class="text-sm" :class="title ? 'mt-1' : ''">{{ message }}</p>
        <slot />
      </div>
      <button v-if="dismissible" class="ml-3 flex-shrink-0 opacity-70 hover:opacity-100" @click="$emit('dismiss')">
        <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </div>
</template>
