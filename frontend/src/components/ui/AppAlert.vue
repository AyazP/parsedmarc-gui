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
      'bg-blue-50 text-blue-800 border border-blue-200': type === 'info' || !type,
      'bg-green-50 text-green-800 border border-green-200': type === 'success',
      'bg-yellow-50 text-yellow-800 border border-yellow-200': type === 'warning',
      'bg-red-50 text-red-800 border border-red-200': type === 'error',
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
