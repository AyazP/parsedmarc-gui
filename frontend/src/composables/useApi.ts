import { ref } from 'vue'

export function useApi<T>(apiFn: (...args: unknown[]) => Promise<T>) {
  const data = ref<T | null>(null) as { value: T | null }
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute(...args: unknown[]): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await apiFn(...args)
      data.value = result
      return result
    } catch (e: unknown) {
      const err = e as { detail?: string; message?: string }
      error.value = err.detail || err.message || 'An error occurred'
      return null
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
