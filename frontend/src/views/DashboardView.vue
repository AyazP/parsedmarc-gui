<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { parsingApi } from '@/api/parsing'
import type { ParseJob } from '@/types/parsing'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const appStore = useAppStore()
const router = useRouter()
const recentJobs = ref<ParseJob[]>([])
const reportsTotal = ref(0)
const loading = ref(true)

const statusVariant = {
  completed: 'success' as const,
  running: 'info' as const,
  pending: 'neutral' as const,
  failed: 'error' as const,
}

onMounted(async () => {
  try {
    const [jobs, reports] = await Promise.all([
      parsingApi.listJobs({ limit: 5 }),
      parsingApi.listReports({ limit: 0 }),
    ])
    recentJobs.value = jobs
    reportsTotal.value = reports.total
  } catch {
    // API may not be available yet
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <template v-else>
      <!-- Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <AppCard>
          <p class="text-sm text-gray-500 dark:text-gray-400">Total Reports</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{{ reportsTotal }}</p>
        </AppCard>
        <AppCard>
          <p class="text-sm text-gray-500 dark:text-gray-400">Recent Jobs</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{{ recentJobs.length }}</p>
        </AppCard>
        <AppCard>
          <p class="text-sm text-gray-500 dark:text-gray-400">System Status</p>
          <div class="flex items-center gap-2 mt-1">
            <span class="w-3 h-3 rounded-full" :class="appStore.health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'" />
            <span class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ appStore.health?.status === 'healthy' ? 'Healthy' : 'Unknown' }}</span>
          </div>
        </AppCard>
      </div>

      <!-- Quick Actions -->
      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Quick Actions</h2>
        </template>
        <div class="flex flex-wrap gap-3">
          <AppButton @click="router.push('/upload')">Upload Report</AppButton>
          <AppButton variant="secondary" @click="router.push('/mailboxes')">Configure Mailbox</AppButton>
          <AppButton variant="secondary" @click="router.push('/outputs')">Configure Output</AppButton>
        </div>
      </AppCard>

      <!-- Recent Jobs -->
      <AppCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Recent Parse Jobs</h2>
            <AppButton variant="ghost" size="sm" @click="router.push('/jobs')">View all</AppButton>
          </div>
        </template>
        <div v-if="recentJobs.length === 0" class="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">No parse jobs yet</div>
        <div v-else class="divide-y divide-gray-100 dark:divide-gray-700">
          <div v-for="job in recentJobs" :key="job.id" class="flex items-center justify-between py-3">
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ job.input_source || job.job_type }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ new Date(job.created_at).toLocaleString() }}</p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {{ job.aggregate_reports_count + job.forensic_reports_count + job.smtp_tls_reports_count }} reports
              </span>
              <AppBadge :variant="statusVariant[job.status] ?? 'neutral'" :text="job.status" />
            </div>
          </div>
        </div>
      </AppCard>
    </template>
  </div>
</template>
