<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  data: unknown
  label?: string
  depth?: number
}>()

const expanded = ref(props.depth === undefined || props.depth < 2)

const isObject = computed(() => props.data !== null && typeof props.data === 'object' && !Array.isArray(props.data))
const isArray = computed(() => Array.isArray(props.data))
const isExpandable = computed(() => isObject.value || isArray.value)

const entries = computed(() => {
  if (isArray.value) {
    return (props.data as unknown[]).map((v, i) => ({ key: String(i), value: v }))
  }
  if (isObject.value) {
    return Object.entries(props.data as Record<string, unknown>).map(([key, value]) => ({ key, value }))
  }
  return []
})

function formatValue(value: unknown): string {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'string') return `"${value}"`
  return String(value)
}

function valueClass(value: unknown): string {
  if (value === null || value === undefined) return 'text-gray-400'
  if (typeof value === 'string') return 'text-green-700'
  if (typeof value === 'number') return 'text-blue-700'
  if (typeof value === 'boolean') return 'text-purple-700'
  return 'text-gray-900'
}
</script>

<template>
  <div class="font-mono text-sm">
    <div
      v-if="isExpandable"
      class="cursor-pointer select-none hover:bg-gray-50 rounded px-1 -mx-1"
      @click="expanded = !expanded"
    >
      <span class="text-gray-400 inline-block w-4">{{ expanded ? '▼' : '▶' }}</span>
      <span v-if="label" class="text-gray-700 font-medium">{{ label }}</span>
      <span class="text-gray-400 ml-1">
        {{ isArray ? '[' + entries.length + ']' : '{' + entries.length + '}' }}
      </span>
    </div>
    <div v-if="isExpandable && expanded" class="ml-4 border-l border-gray-200 pl-3">
      <div v-for="entry in entries" :key="entry.key">
        <ReportJsonViewer
          v-if="entry.value !== null && typeof entry.value === 'object'"
          :data="entry.value"
          :label="entry.key"
          :depth="(depth ?? 0) + 1"
        />
        <div v-else class="py-0.5">
          <span class="text-gray-700 font-medium">{{ entry.key }}</span>
          <span class="text-gray-400">: </span>
          <span :class="valueClass(entry.value)">{{ formatValue(entry.value) }}</span>
        </div>
      </div>
    </div>
    <div v-if="!isExpandable" class="py-0.5">
      <span v-if="label" class="text-gray-700 font-medium">{{ label }}: </span>
      <span :class="valueClass(data)">{{ formatValue(data) }}</span>
    </div>
  </div>
</template>
