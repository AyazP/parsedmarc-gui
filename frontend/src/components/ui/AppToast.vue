<script setup lang="ts">
defineProps<{
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
}>()

defineEmits<{
  dismiss: []
}>()
</script>

<template>
  <div
    class="flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg text-sm"
    :class="{
      'bg-green-600 text-white': type === 'success',
      'bg-red-600 text-white': type === 'error',
      'bg-blue-600 text-white': type === 'info',
      'bg-yellow-500 text-white': type === 'warning',
    }"
  >
    <span class="flex-1">{{ message }}</span>
    <button class="opacity-70 hover:opacity-100 flex-shrink-0" @click="$emit('dismiss')">
      <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
</template>
