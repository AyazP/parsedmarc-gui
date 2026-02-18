<script setup lang="ts">
import { computed } from 'vue'
import { useSetupStore } from '@/stores/setup'
import AppCard from '@/components/ui/AppCard.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'

const setupStore = useSetupStore()

const dbSummary = computed(() => {
  const d = setupStore.wizardData
  const dbType = d.db_type || 'sqlite'
  if (dbType === 'sqlite') {
    return `SQLite — ${d.db_path || './data/parsedmarc.db'}`
  }
  const label = dbType === 'postgresql' ? 'PostgreSQL' : 'MySQL'
  return `${label} — ${d.db_user || '?'}@${d.db_host || '?'}:${d.db_port || '?'}/${d.db_name || '?'}`
})

async function complete() {
  await setupStore.completeSetup()
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Review & Complete</h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">Review your configuration before completing the setup.</p>
    </div>

    <div class="grid gap-4">
      <AppCard>
        <template #header><h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Encryption</h3></template>
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ setupStore.wizardData.encryption_key ? 'Key configured' : 'Key will be auto-generated' }}</p>
      </AppCard>

      <AppCard>
        <template #header><h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Admin Account</h3></template>
        <p class="text-sm text-gray-600 dark:text-gray-400">Username: <strong>{{ setupStore.wizardData.admin_username || '(not set)' }}</strong></p>
      </AppCard>

      <AppCard>
        <template #header><h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">SSL/TLS</h3></template>
        <p class="text-sm text-gray-600 dark:text-gray-400">Type: <strong>{{ setupStore.wizardData.ssl_type }}</strong></p>
      </AppCard>

      <AppCard>
        <template #header><h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Server</h3></template>
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ setupStore.wizardData.host }}:{{ setupStore.wizardData.port }} &middot; Log: {{ setupStore.wizardData.log_level }}</p>
      </AppCard>

      <AppCard>
        <template #header><h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">Database</h3></template>
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ dbSummary }}</p>
      </AppCard>
    </div>

    <AppAlert v-if="setupStore.error" type="error" :message="setupStore.error" />

    <div v-if="setupStore.completionResult" class="space-y-3">
      <AppAlert type="success" title="Setup Complete!" message="The application has been configured. A restart may be required for some changes to take effect." />
      <div v-if="(setupStore.completionResult as Record<string, unknown>)?.encryption_key" class="p-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
        <p class="text-sm font-medium text-yellow-800 dark:text-yellow-200">Save this encryption key now:</p>
        <code class="block mt-2 text-sm font-mono break-all select-all">{{ (setupStore.completionResult as Record<string, unknown>).encryption_key }}</code>
      </div>
    </div>

    <AppButton v-if="!setupStore.completionResult" variant="primary" size="lg" :loading="setupStore.loading" @click="complete">
      Complete Setup
    </AppButton>
  </div>
</template>
