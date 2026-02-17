<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useParsingStore } from '@/stores/parsing'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import DataTable from '@/components/data/DataTable.vue'
import FilterBar from '@/components/data/FilterBar.vue'

const store = useParsingStore()
const statusFilter = ref('')

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
]

const statusVariant: Record<string, 'success' | 'info' | 'neutral' | 'error'> = {
  completed: 'success',
  running: 'info',
  pending: 'neutral',
  failed: 'error',
}

const columns = [
  { key: 'id', label: 'ID', class: 'w-16' },
  { key: 'job_type', label: 'Type' },
  { key: 'input_source', label: 'Source' },
  { key: 'status', label: 'Status' },
  { key: 'reports', label: 'Reports' },
  { key: 'error_message', label: 'Error' },
  { key: 'created_at', label: 'Created' },
  { key: 'completed_at', label: 'Completed' },
]

function loadJobs() {
  store.fetchJobs({
    limit: 100,
    status: statusFilter.value || undefined,
  })
}

onMounted(() => {
  loadJobs()
})

function applyFilter() {
  loadJobs()
}

function formatReports(row: Record<string, unknown>): string {
  const agg = Number(row.aggregate_reports_count || 0)
  const for_ = Number(row.forensic_reports_count || 0)
  const tls = Number(row.smtp_tls_reports_count || 0)
  const total = agg + for_ + tls
  if (total === 0) return '-'
  const parts: string[] = []
  if (agg) parts.push(`${agg} agg`)
  if (for_) parts.push(`${for_} for`)
  if (tls) parts.push(`${tls} tls`)
  return parts.join(', ')
}

function formatDate(dateStr: unknown): string {
  if (!dateStr) return '-'
  return new Date(String(dateStr)).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Parse Jobs</h1>

    <AppCard>
      <FilterBar>
        <AppSelect
          :model-value="statusFilter"
          :options="statusOptions"
          placeholder="Status"
          @update:model-value="statusFilter = $event"
        />
        <AppButton size="sm" @click="applyFilter">Apply</AppButton>
        <AppButton size="sm" variant="secondary" @click="loadJobs">Refresh</AppButton>
      </FilterBar>
    </AppCard>

    <AppCard>
      <DataTable
        :columns="columns"
        :rows="(store.jobs as Record<string, unknown>[])"
        :loading="store.jobsLoading"
      >
        <template #cell-id="{ value }">
          <span class="font-mono text-xs">#{{ value }}</span>
        </template>
        <template #cell-job_type="{ value }">
          <AppBadge :text="String(value)" variant="info" />
        </template>
        <template #cell-input_source="{ value }">
          {{ value ?? '-' }}
        </template>
        <template #cell-status="{ value }">
          <AppBadge :text="String(value)" :variant="statusVariant[String(value)] ?? 'neutral'" />
        </template>
        <template #cell-reports="{ row }">
          {{ formatReports(row) }}
        </template>
        <template #cell-error_message="{ value }">
          <span v-if="value" class="text-xs text-red-600 max-w-[200px] truncate block">{{ value }}</span>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #cell-created_at="{ value }">
          {{ formatDate(value) }}
        </template>
        <template #cell-completed_at="{ value }">
          {{ formatDate(value) }}
        </template>
      </DataTable>
    </AppCard>
  </div>
</template>
