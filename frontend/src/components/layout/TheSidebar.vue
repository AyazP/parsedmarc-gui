<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import SidebarNavItem from './SidebarNavItem.vue'

const appStore = useAppStore()

const navItems = [
  { to: '/', label: 'Dashboard', icon: 'D' },
  { to: '/mailboxes', label: 'Mailboxes', icon: 'M' },
  { to: '/outputs', label: 'Outputs', icon: 'O' },
  { to: '/reports', label: 'Reports', icon: 'R' },
  { to: '/jobs', label: 'Jobs', icon: 'J' },
  { to: '/upload', label: 'Upload', icon: 'U' },
  { to: '/settings', label: 'Settings', icon: 'S' },
]
</script>

<template>
  <aside
    class="flex flex-col bg-white border-r border-gray-200 h-screen sticky top-0 transition-all duration-200"
    :class="appStore.sidebarCollapsed ? 'w-16' : 'w-60'"
  >
    <!-- Brand -->
    <div class="flex items-center gap-3 px-4 h-16 border-b border-gray-200 flex-shrink-0">
      <div class="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold text-sm">P</div>
      <span v-if="!appStore.sidebarCollapsed" class="font-semibold text-gray-900 truncate">ParseDMARC</span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
      <SidebarNavItem
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :label="item.label"
        :icon="item.icon"
        :collapsed="appStore.sidebarCollapsed"
      />
    </nav>

    <!-- Collapse toggle -->
    <div class="px-2 py-3 border-t border-gray-200 flex-shrink-0">
      <button
        class="flex items-center justify-center w-full rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
        @click="appStore.toggleSidebar()"
      >
        <svg class="w-5 h-5 transition-transform" :class="appStore.sidebarCollapsed ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
        <span v-if="!appStore.sidebarCollapsed" class="ml-2">Collapse</span>
      </button>
    </div>
  </aside>
</template>
