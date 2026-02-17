import { ref } from 'vue'
import { defineStore } from 'pinia'
import { mailboxApi } from '@/api/mailboxes'
import type {
  MailboxConfig,
  MailboxConfigCreate,
  MailboxConfigUpdate,
  ConnectionTestResult,
} from '@/types/mailbox'

export const useMailboxStore = defineStore('mailboxes', () => {
  const configs = ref<MailboxConfig[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchConfigs() {
    loading.value = true
    error.value = null
    try {
      configs.value = await mailboxApi.list()
    } catch (e: unknown) {
      const err = e as { detail?: string; message?: string }
      error.value = err.detail || err.message || 'Failed to load mailbox configs'
    } finally {
      loading.value = false
    }
  }

  async function getConfig(id: number): Promise<MailboxConfig | null> {
    try {
      return await mailboxApi.get(id)
    } catch {
      return null
    }
  }

  async function createConfig(data: MailboxConfigCreate): Promise<MailboxConfig> {
    const config = await mailboxApi.create(data)
    configs.value.push(config)
    return config
  }

  async function updateConfig(id: number, data: MailboxConfigUpdate): Promise<MailboxConfig> {
    const config = await mailboxApi.update(id, data)
    const idx = configs.value.findIndex((c) => c.id === id)
    if (idx !== -1) configs.value[idx] = config
    return config
  }

  async function deleteConfig(id: number): Promise<void> {
    await mailboxApi.delete(id)
    configs.value = configs.value.filter((c) => c.id !== id)
  }

  async function testConnection(id: number): Promise<ConnectionTestResult> {
    return await mailboxApi.testConnection(id)
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
    testConnection,
  }
})
