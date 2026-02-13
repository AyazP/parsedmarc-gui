import { ref } from 'vue'
import { defineStore } from 'pinia'
import { outputApi } from '@/api/outputs'
import type { OutputConfig, OutputConfigCreate, OutputConfigUpdate } from '@/types/output'

export const useOutputStore = defineStore('outputs', () => {
  const configs = ref<OutputConfig[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchConfigs() {
    loading.value = true
    error.value = null
    try {
      configs.value = await outputApi.list()
    } catch (e: unknown) {
      const err = e as { detail?: string; message?: string }
      error.value = err.detail || err.message || 'Failed to load output configs'
    } finally {
      loading.value = false
    }
  }

  async function getConfig(id: number): Promise<OutputConfig | null> {
    try {
      return await outputApi.get(id)
    } catch {
      return null
    }
  }

  async function createConfig(data: OutputConfigCreate): Promise<OutputConfig> {
    const config = await outputApi.create(data)
    configs.value.push(config)
    return config
  }

  async function updateConfig(id: number, data: OutputConfigUpdate): Promise<OutputConfig> {
    const config = await outputApi.update(id, data)
    const idx = configs.value.findIndex((c) => c.id === id)
    if (idx !== -1) configs.value[idx] = config
    return config
  }

  async function deleteConfig(id: number): Promise<void> {
    await outputApi.delete(id)
    configs.value = configs.value.filter((c) => c.id !== id)
  }

  return {
    configs,
    loading,
    error,
    fetchConfigs,
    getConfig,
    createConfig,
    updateConfig,
    deleteConfig,
  }
})
