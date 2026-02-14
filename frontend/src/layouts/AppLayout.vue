<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import TheSidebar from '@/components/layout/TheSidebar.vue'
import TheTopbar from '@/components/layout/TheTopbar.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const appStore = useAppStore()

onMounted(() => {
  if (!appStore.initialized) {
    appStore.initialize()
  }
})
</script>

<template>
  <div class="flex min-h-screen bg-gray-50">
    <TheSidebar />
    <div class="flex-1 flex flex-col min-w-0">
      <TheTopbar />
      <main class="flex-1 p-6 overflow-auto">
        <slot />
      </main>
    </div>
    <ToastContainer />
  </div>
</template>
