<script setup lang="ts">
import { onMounted } from 'vue'
import { useUpdateStore } from '@/stores/updates'
import { useToast } from '@/composables/useToast'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'

const updateStore = useUpdateStore()
const toast = useToast()

onMounted(async () => {
  await Promise.all([
    updateStore.fetchStatus(),
    updateStore.fetchSettings(),
  ])
})

async function handleCheckNow() {
  await updateStore.checkNow()
  if (updateStore.status?.error) {
    toast.error('Update check failed: ' + updateStore.status.error)
  } else if (updateStore.status?.update_available) {
    toast.info('Update available: v' + updateStore.status.latest_version)
  } else {
    toast.success('You are running the latest version.')
  }
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <AppCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Update Checker</h2>
        <AppButton
          size="sm"
          variant="secondary"
          :loading="updateStore.loading"
          @click="handleCheckNow"
        >
          Check Now
        </AppButton>
      </div>
    </template>
    <div class="space-y-3">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Current Version</p>
          <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
            {{ updateStore.status?.current_version ?? '...' }}
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Latest Version</p>
          <div class="flex items-center gap-2">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
              {{ updateStore.status?.latest_version ?? '...' }}
            </p>
            <AppBadge
              v-if="updateStore.status?.update_available"
              text="Update Available"
              variant="warning"
            />
            <AppBadge
              v-else-if="updateStore.status && !updateStore.status.error"
              text="Up to Date"
              variant="success"
            />
          </div>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Last Checked</p>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ formatDate(updateStore.status?.checked_at) }}
          </p>
        </div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Auto-Check</p>
          <p class="text-sm text-gray-900 dark:text-gray-100">
            {{ updateStore.settings?.enabled ? 'Enabled' : 'Disabled' }}
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Check Interval</p>
          <p class="text-sm text-gray-900 dark:text-gray-100">
            Every {{ updateStore.settings?.interval_hours ?? '...' }} hours
          </p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Deployment Type</p>
          <p class="text-sm text-gray-900 dark:text-gray-100">
            {{ updateStore.status?.is_docker ? 'Docker' : 'Standalone (Git)' }}
          </p>
        </div>
      </div>
    </div>
  </AppCard>
</template>
