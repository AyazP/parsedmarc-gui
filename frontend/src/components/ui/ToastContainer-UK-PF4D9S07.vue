<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import AppToast from './AppToast.vue'

const appStore = useAppStore()
</script>

<template>
  <div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
    <TransitionGroup
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0 translate-x-8"
      leave-to-class="opacity-0 translate-x-8"
    >
      <div v-for="toast in appStore.toasts" :key="toast.id" class="pointer-events-auto">
        <AppToast :type="toast.type" :message="toast.message" @dismiss="appStore.removeToast(toast.id)" />
      </div>
    </TransitionGroup>
  </div>
</template>
