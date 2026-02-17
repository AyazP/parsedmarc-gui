<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps<{
  to: string
  label: string
  icon?: string
  collapsed?: boolean
}>()

const route = useRoute()
const isActive = computed(() => {
  if (props.to === '/') return route.path === '/'
  return route.path === props.to || route.path.startsWith(props.to + '/')
})
</script>

<template>
  <RouterLink
    :to="to"
    class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
    :class="isActive ? 'bg-primary-600/20 text-primary-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'"
    :title="collapsed ? label : undefined"
  >
    <svg v-if="icon" class="flex-shrink-0 w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" :d="icon" />
    </svg>
    <span v-if="!collapsed" class="truncate">{{ label }}</span>
  </RouterLink>
</template>
