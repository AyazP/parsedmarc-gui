import { useAppStore } from '@/stores/app'

export function useToast() {
  const appStore = useAppStore()

  return {
    success: (message: string) => appStore.addToast({ type: 'success', message, timeout: 4000 }),
    error: (message: string) => appStore.addToast({ type: 'error', message, timeout: 6000 }),
    info: (message: string) => appStore.addToast({ type: 'info', message, timeout: 4000 }),
    warning: (message: string) => appStore.addToast({ type: 'warning', message, timeout: 5000 }),
  }
}
