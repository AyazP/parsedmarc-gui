<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useParsingStore } from '@/stores/parsing'
import { useToast } from '@/composables/useToast'
import type { ParsedReport } from '@/types/parsing'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import ReportJsonViewer from '@/components/report/ReportJsonViewer.vue'

const route = useRoute()
const router = useRouter()
const store = useParsingStore()
const toast = useToast()

const report = ref<ParsedReport | null>(null)
const loading = ref(true)

const typeVariant: Record<string, 'success' | 'warning' | 'info' | 'neutral'> = {
  aggregate: 'success',
  forensic: 'warning',
  smtp_tls: 'info',
}

onMounted(async () => {
  const id = Number(route.params.id)
  const result = await store.getReport(id)
  if (!result) {
    toast.error('Report not found.')
    router.replace('/reports')
    return
  }
  report.value = result
  loading.value = false
})

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <AppButton variant="ghost" @click="router.push('/reports')">
        &larr; Back
      </AppButton>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Report Detail</h1>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <template v-else-if="report">
      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Metadata</h2>
        </template>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">Type</p>
            <AppBadge :text="report.report_type" :variant="typeVariant[report.report_type] ?? 'neutral'" />
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">Organization</p>
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ report.org_name ?? '-' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">Domain</p>
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ report.domain ?? '-' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">Report ID</p>
            <p class="text-sm font-mono text-gray-600 dark:text-gray-400 break-all">{{ report.report_id ?? '-' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">Date Range</p>
            <p class="text-sm text-gray-900 dark:text-gray-100">
              {{ formatDate(report.date_begin) }} — {{ formatDate(report.date_end) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400">Imported</p>
            <p class="text-sm text-gray-900 dark:text-gray-100">{{ formatDate(report.created_at) }}</p>
          </div>
        </div>
      </AppCard>

      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Report Data</h2>
        </template>
        <ReportJsonViewer :data="report.report_json" />
      </AppCard>
    </template>
  </div>
</template>
