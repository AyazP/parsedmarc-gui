<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useParsingStore } from '@/stores/parsing'
import { usePagination } from '@/composables/usePagination'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import DataTable from '@/components/data/DataTable.vue'
import Pagination from '@/components/data/Pagination.vue'
import FilterBar from '@/components/data/FilterBar.vue'

const router = useRouter()
const store = useParsingStore()
const pagination = usePagination(25)

const typeOptions = [
  { value: '', label: 'All Types' },
  { value: 'aggregate', label: 'Aggregate' },
  { value: 'forensic', label: 'Forensic' },
  { value: 'smtp_tls', label: 'SMTP TLS' },
]

const typeVariant: Record<string, 'success' | 'info' | 'warning' | 'neutral'> = {
  aggregate: 'success',
  forensic: 'warning',
  smtp_tls: 'info',
}

const columns = [
  { key: 'report_type', label: 'Type' },
  { key: 'org_name', label: 'Organization' },
  { key: 'domain', label: 'Domain' },
  { key: 'report_id', label: 'Report ID' },
  { key: 'date_begin', label: 'Date Range' },
  { key: 'created_at', label: 'Imported' },
  { key: 'actions', label: '', class: 'w-20 text-right' },
]

function loadReports() {
  store.fetchReports({
    skip: pagination.skip.value,
    limit: pagination.pageSize.value,
    report_type: store.filters.report_type || undefined,
    domain: store.filters.domain || undefined,
    org_name: store.filters.org_name || undefined,
  })
}

onMounted(() => {
  loadReports()
})

watch(() => store.reportsTotal, (val) => {
  pagination.setTotal(val)
})

watch(() => pagination.currentPage.value, () => {
  loadReports()
})

function applyFilters() {
  pagination.goToPage(1)
  loadReports()
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Reports</h1>

    <AppCard>
      <template #header>
        <h2 class="text-base font-semibold text-gray-900">Filters</h2>
      </template>
      <FilterBar>
        <AppSelect
          :model-value="store.filters.report_type ?? ''"
          :options="typeOptions"
          placeholder="Report Type"
          @update:model-value="store.filters.report_type = $event || undefined"
        />
        <AppInput
          :model-value="store.filters.domain ?? ''"
          placeholder="Filter by domain..."
          @update:model-value="store.filters.domain = $event || undefined"
        />
        <AppInput
          :model-value="store.filters.org_name ?? ''"
          placeholder="Filter by organization..."
          @update:model-value="store.filters.org_name = $event || undefined"
        />
        <AppButton size="sm" @click="applyFilters">Apply</AppButton>
      </FilterBar>
    </AppCard>

    <AppCard>
      <DataTable
        :columns="columns"
        :rows="(store.reports as Record<string, unknown>[])"
        :loading="store.reportsLoading"
      >
        <template #cell-report_type="{ value }">
          <AppBadge :text="String(value)" :variant="typeVariant[String(value)] ?? 'neutral'" />
        </template>
        <template #cell-org_name="{ value }">
          {{ value ?? '-' }}
        </template>
        <template #cell-domain="{ value }">
          {{ value ?? '-' }}
        </template>
        <template #cell-report_id="{ value }">
          <span class="text-xs font-mono text-gray-500 max-w-[200px] truncate block">{{ value ?? '-' }}</span>
        </template>
        <template #cell-date_begin="{ row }">
          {{ formatDate(row.date_begin as string | null) }} — {{ formatDate(row.date_end as string | null) }}
        </template>
        <template #cell-created_at="{ value }">
          {{ new Date(String(value)).toLocaleString() }}
        </template>
        <template #cell-actions="{ row }">
          <AppButton size="sm" variant="ghost" @click="router.push(`/reports/${row.id}`)">View</AppButton>
        </template>
      </DataTable>
      <Pagination
        :current-page="pagination.currentPage.value"
        :total-pages="pagination.totalPages.value"
        :total="pagination.total.value"
        @page-change="pagination.goToPage($event); loadReports()"
      />
    </AppCard>
  </div>
</template>
