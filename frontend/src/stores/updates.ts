import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { updatesApi } from '@/api/updates'
import type { UpdateStatus, UpdateSettings } from '@/types/updates'

export const useUpdateStore = defineStore('updates', () => {
  const status = ref<UpdateStatus | null>(null)
  const settings = ref<UpdateSettings | null>(null)
  const loading = ref(false)
  const dismissed = ref(false)

  const updateAvailable = computed(() =>
    status.value?.update_available === true && !dismissed.value
  )

  async function fetchStatus() {
    try {
      status.value = await updatesApi.getStatus()
    } catch {
      status.value = null
    }
  }

  async function checkNow() {
    loading.value = true
    try {
      status.value = await updatesApi.checkNow()
      dismissed.value = false
    } catch {
      // Silently fail - update checking is non-critical
    } finally {
      loading.value = false
    }
  }

  async function fetchSettings() {
    try {
      settings.value = await updatesApi.getSettings()
    } catch {
      settings.value = null
    }
  }

  function dismiss() {
    dismissed.value = true
  }

  return {
    status,
    settings,
    loading,
    dismissed,
    updateAvailable,
    fetchStatus,
    checkNow,
    fetchSettings,
    dismiss,
  }
})
