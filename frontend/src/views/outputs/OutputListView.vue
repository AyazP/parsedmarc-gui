<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOutputStore } from '@/stores/outputs'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppModal from '@/components/ui/AppModal.vue'
import DataTable from '@/components/data/DataTable.vue'

const router = useRouter()
const store = useOutputStore()
const toast = useToast()
const { isOpen, title, message, confirm, handleConfirm, handleCancel } = useConfirmDialog()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Type' },
  { key: 'enabled', label: 'Status' },
  { key: 'report_types', label: 'Report Types' },
  { key: 'actions', label: '', class: 'w-36 text-right' },
]

onMounted(() => {
  store.fetchConfigs()
})

async function handleDelete(id: number, name: string) {
  const ok = await confirm('Delete Output', `Are you sure you want to delete "${name}"? This cannot be undone.`)
  if (!ok) return
  try {
    await store.deleteConfig(id)
    toast.success('Output config deleted.')
  } catch {
    toast.error('Failed to delete output config.')
  }
}

function getReportTypes(row: Record<string, unknown>): string[] {
  const types: string[] = []
  if (row.save_aggregate) types.push('Aggregate')
  if (row.save_forensic) types.push('Forensic')
  if (row.save_smtp_tls) types.push('SMTP TLS')
  return types
}

const typeLabels: Record<string, string> = {
  elasticsearch: 'Elasticsearch',
  opensearch: 'OpenSearch',
  splunk: 'Splunk',
  kafka: 'Kafka',
  s3: 'S3',
  syslog: 'Syslog',
  gelf: 'GELF',
  webhook: 'Webhook',
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">Output Configs</h1>
      <AppButton @click="router.push('/outputs/new')">Add Output</AppButton>
    </div>

    <AppCard>
      <DataTable :columns="columns" :rows="(store.configs as Record<string, unknown>[])" :loading="store.loading">
        <template #cell-type="{ value }">
          <AppBadge :text="typeLabels[String(value)] ?? String(value)" variant="info" />
        </template>
        <template #cell-enabled="{ value }">
          <AppBadge :text="value ? 'Enabled' : 'Disabled'" :variant="value ? 'success' : 'neutral'" />
        </template>
        <template #cell-report_types="{ row }">
          <div class="flex gap-1">
            <AppBadge v-for="t in getReportTypes(row)" :key="t" :text="t" variant="neutral" />
          </div>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex items-center justify-end gap-2">
            <AppButton size="sm" variant="secondary" @click="router.push(`/outputs/${row.id}/edit`)">Edit</AppButton>
            <AppButton size="sm" variant="danger" @click="handleDelete(Number(row.id), String(row.name))">Delete</AppButton>
          </div>
        </template>
      </DataTable>
    </AppCard>

    <!-- Confirm Dialog -->
    <AppModal :open="isOpen" :title="title" @close="handleCancel">
      <p class="text-sm text-gray-600">{{ message }}</p>
      <template #footer>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" @click="handleCancel">Cancel</AppButton>
          <AppButton variant="danger" @click="handleConfirm">Delete</AppButton>
        </div>
      </template>
    </AppModal>
  </div>
</template>
