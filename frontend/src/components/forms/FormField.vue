<script setup lang="ts">
defineProps<{
  label?: string
  error?: string
  helpText?: string
}>()
</script>

<template>
  <div>
    <label v-if="label" class="block text-sm font-medium text-gray-700 mb-1">{{ label }}</label>
    <slot />
    <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
    <p v-else-if="helpText" class="mt-1 text-sm text-gray-500">{{ helpText }}</p>
  </div>
</template>
