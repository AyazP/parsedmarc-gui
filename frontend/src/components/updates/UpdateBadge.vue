<script setup lang="ts">
import { ref } from 'vue'
import { useUpdateStore } from '@/stores/updates'
import UpdateModal from './UpdateModal.vue'

const updateStore = useUpdateStore()
const showModal = ref(false)
</script>

<template>
  <button
    v-if="updateStore.updateAvailable"
    class="relative flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 hover:bg-amber-100 dark:hover:bg-amber-900/50 transition-colors"
    @click="showModal = true"
  >
    <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clip-rule="evenodd" />
    </svg>
    <span>Update Available</span>
    <span class="inline-flex items-center rounded-full bg-amber-200 dark:bg-amber-800 px-1.5 py-0.5 text-xs font-medium text-amber-800 dark:text-amber-200">
      {{ updateStore.status?.latest_version }}
    </span>
  </button>

  <UpdateModal :open="showModal" @close="showModal = false" />
</template>
