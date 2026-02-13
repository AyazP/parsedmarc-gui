<script setup lang="ts">
defineProps<{
  padding?: boolean
}>()
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div v-if="$slots.header" class="px-6 py-4 border-b border-gray-200">
      <slot name="header" />
    </div>
    <div :class="padding !== false ? 'px-6 py-4' : ''">
      <slot />
    </div>
    <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
      <slot name="footer" />
    </div>
  </div>
</template>
