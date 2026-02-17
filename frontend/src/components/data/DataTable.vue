<script setup lang="ts">
import AppSpinner from '@/components/ui/AppSpinner.vue'

defineProps<{
  columns: { key: string; label: string; class?: string }[]
  rows: Record<string, unknown>[]
  loading?: boolean
}>()
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
      <thead class="bg-gray-50 dark:bg-gray-800">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
            :class="col.class"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
        <tr v-if="loading">
          <td :colspan="columns.length" class="px-4 py-8 text-center">
            <AppSpinner class="mx-auto" />
          </td>
        </tr>
        <tr v-else-if="rows.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            No data available
          </td>
        </tr>
        <tr v-for="(row, idx) in rows" v-else :key="idx" class="hover:bg-gray-50 dark:hover:bg-gray-700">
          <td v-for="col in columns" :key="col.key" class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100" :class="col.class">
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              {{ row[col.key] ?? '-' }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
