import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemApi } from '@/api/system'
import type { HealthStatus, SystemInfo } from '@/types/system'

export interface ToastNotification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  timeout?: number
}

let toastCounter = 0

export const useAppStore = defineStore('app', () => {
  const health = ref<HealthStatus | null>(null)
  const systemInfo = ref<SystemInfo | null>(null)
  const sidebarCollapsed = ref(false)
  const toasts = ref<ToastNotification[]>([])
  const initialized = ref(false)
  const darkMode = ref(false)

  async function fetchHealth() {
    try {
      health.value = await systemApi.health()
    } catch {
      health.value = null
    }
  }

  async function fetchSystemInfo() {
    try {
      systemInfo.value = await systemApi.systemInfo()
    } catch {
      systemInfo.value = null
    }
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function initDarkMode() {
    const stored = localStorage.getItem('parsedmarc-dark-mode')
    if (stored !== null) {
      darkMode.value = stored === 'true'
    } else {
      darkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    applyDarkMode()
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    localStorage.setItem('parsedmarc-dark-mode', String(darkMode.value))
    applyDarkMode()
  }

  function applyDarkMode() {
    document.documentElement.classList.toggle('dark', darkMode.value)
  }

  function addToast(toast: Omit<ToastNotification, 'id'>) {
    const id = `toast_${++toastCounter}`
    toasts.value.push({ ...toast, id })
    if (toast.timeout) {
      setTimeout(() => removeToast(id), toast.timeout)
    }
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  async function initialize() {
    initDarkMode()
    await Promise.all([fetchHealth(), fetchSystemInfo()])
    initialized.value = true
  }

  return {
    health,
    systemInfo,
    sidebarCollapsed,
    toasts,
    initialized,
    darkMode,
    fetchHealth,
    fetchSystemInfo,
    toggleSidebar,
    initDarkMode,
    toggleDarkMode,
    addToast,
    removeToast,
    initialize,
  }
})
