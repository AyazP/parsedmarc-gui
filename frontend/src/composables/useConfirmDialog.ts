import { ref } from 'vue'

export function useConfirmDialog() {
  const isOpen = ref(false)
  const title = ref('')
  const message = ref('')
  let resolvePromise: ((value: boolean) => void) | null = null

  function confirm(t: string, m: string): Promise<boolean> {
    title.value = t
    message.value = m
    isOpen.value = true
    return new Promise((resolve) => {
      resolvePromise = resolve
    })
  }

  function handleConfirm() {
    isOpen.value = false
    resolvePromise?.(true)
  }

  function handleCancel() {
    isOpen.value = false
    resolvePromise?.(false)
  }

  return { isOpen, title, message, confirm, handleConfirm, handleCancel }
}
