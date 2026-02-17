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
const isActive = computed(() => route.path === props.to || route.path.startsWith(props.to + '/'))
</script>

<template>
  <RouterLink
    :to="to"
    class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
    :class="isActive ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
    :title="collapsed ? label : undefined"
  >
    <span class="flex-shrink-0 w-5 h-5 flex items-center justify-center text-base">{{ icon }}</span>
    <span v-if="!collapsed" class="truncate">{{ label }}</span>
  </RouterLink>
</template>
