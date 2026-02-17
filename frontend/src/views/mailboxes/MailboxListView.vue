<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMailboxStore } from '@/stores/mailboxes'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import type { ConnectionTestResult } from '@/types/mailbox'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppModal from '@/components/ui/AppModal.vue'
import DataTable from '@/components/data/DataTable.vue'

const router = useRouter()
const store = useMailboxStore()
const toast = useToast()
const { isOpen, title, message, confirm, handleConfirm, handleCancel } = useConfirmDialog()

const testingId = ref<number | null>(null)
const testResult = ref<ConnectionTestResult | null>(null)
const testModalOpen = ref(false)

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Type' },
  { key: 'enabled', label: 'Status' },
  { key: 'watch_interval', label: 'Interval' },
  { key: 'actions', label: '', class: 'w-48 text-right' },
]

onMounted(() => {
  store.fetchConfigs()
})

async function handleDelete(id: number, name: string) {
  const ok = await confirm('Delete Mailbox', `Are you sure you want to delete "${name}"? This cannot be undone.`)
  if (!ok) return
  try {
    await store.deleteConfig(id)
    toast.success('Mailbox config deleted.')
  } catch {
    toast.error('Failed to delete mailbox config.')
  }
}

async function handleTest(id: number) {
  testingId.value = id
  testResult.value = null
  testModalOpen.value = true
  try {
    testResult.value = await store.testConnection(id)
  } catch {
    testResult.value = { success: false, message: 'Connection test failed. Check server logs for details.' }
  } finally {
    testingId.value = null
  }
}

function formatInterval(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${Math.round(seconds / 3600)}h`
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Mailbox Configs</h1>
      <AppButton @click="router.push('/mailboxes/new')">Add Mailbox</AppButton>
    </div>

    <AppCard>
      <DataTable :columns="columns" :rows="(store.configs as Record<string, unknown>[])" :loading="store.loading">
        <template #cell-type="{ value }">
          <AppBadge :text="String(value).toUpperCase()" variant="info" />
        </template>
        <template #cell-enabled="{ value }">
          <AppBadge :text="value ? 'Enabled' : 'Disabled'" :variant="value ? 'success' : 'neutral'" />
        </template>
        <template #cell-watch_interval="{ value }">
          {{ formatInterval(Number(value)) }}
        </template>
        <template #cell-actions="{ row }">
          <div class="flex items-center justify-end gap-2">
            <AppButton size="sm" variant="ghost" @click="handleTest(Number(row.id))">Test</AppButton>
            <AppButton size="sm" variant="secondary" @click="router.push(`/mailboxes/${row.id}/edit`)">Edit</AppButton>
            <AppButton size="sm" variant="danger" @click="handleDelete(Number(row.id), String(row.name))">Delete</AppButton>
          </div>
        </template>
      </DataTable>
    </AppCard>

    <!-- Confirm Dialog -->
    <AppModal :open="isOpen" :title="title" @close="handleCancel">
      <p class="text-sm text-gray-600 dark:text-gray-400">{{ message }}</p>
      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" @click="handleCancel">Cancel</AppButton>
          <AppButton variant="danger" @click="handleConfirm">Delete</AppButton>
        </div>
      </template>
    </AppModal>

    <!-- Test Connection Modal -->
    <AppModal :open="testModalOpen" title="Connection Test" @close="testModalOpen = false">
      <div v-if="testingId !== null" class="flex items-center gap-3 py-4">
        <svg class="animate-spin h-5 w-5 text-primary-600 dark:text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span class="text-sm text-gray-600 dark:text-gray-400">Testing connection...</span>
      </div>
      <div v-else-if="testResult" class="space-y-3">
        <div class="flex items-center gap-2">
          <span
            class="w-3 h-3 rounded-full"
            :class="testResult.success ? 'bg-green-500' : 'bg-red-500'"
          />
          <span class="text-sm font-medium" :class="testResult.success ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'">
            {{ testResult.success ? 'Success' : 'Failed' }}
          </span>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ testResult.message }}</p>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <AppButton variant="secondary" @click="testModalOpen = false">Close</AppButton>
        </div>
      </template>
    </AppModal>
  </div>
</template>
