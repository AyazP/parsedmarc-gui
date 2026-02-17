<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  currentPage: number
  totalPages: number
  total: number
}>()

const emit = defineEmits<{
  'page-change': [page: number]
}>()

const pages = computed(() => {
  const p: number[] = []
  const start = Math.max(1, props.currentPage - 2)
  const end = Math.min(props.totalPages, props.currentPage + 2)
  for (let i = start; i <= end; i++) p.push(i)
  return p
})
</script>

<template>
  <div class="flex items-center justify-between px-4 py-3">
    <p class="text-sm text-gray-700 dark:text-gray-300">
      {{ total }} result{{ total !== 1 ? 's' : '' }}
    </p>
    <div v-if="totalPages > 1" class="flex items-center gap-1">
      <button
        class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="currentPage <= 1"
        @click="emit('page-change', currentPage - 1)"
      >
        Prev
      </button>
      <button
        v-for="page in pages"
        :key="page"
        class="px-3 py-1.5 text-sm rounded-lg"
        :class="page === currentPage ? 'bg-primary-600 text-white' : 'border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'"
        @click="emit('page-change', page)"
      >
        {{ page }}
      </button>
      <button
        class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="currentPage >= totalPages"
        @click="emit('page-change', currentPage + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>
