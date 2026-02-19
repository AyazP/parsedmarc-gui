<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSetupStore } from '@/stores/setup'
import { setupApi } from '@/api/setup'
import AppCard from '@/components/ui/AppCard.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'

const setupStore = useSetupStore()
const restarting = ref(false)
const restartError = ref('')
const restartReady = ref(false)
const countdown = ref(0)

const dbSummary = computed(() => {
  const d = setupStore.wizardData
  const dbType = d.db_type || 'sqlite'
  if (dbType === 'sqlite') {
    return `SQLite — ${d.db_path || './data/parsedmarc.db'}`
  }
  const label = dbType === 'postgresql' ? 'PostgreSQL' : 'MySQL'
  return `${label} — ${d.db_user || '?'}@${d.db_host || '?'}:${d.db_port || '?'}/${d.db_name || '?'}`
})

const needsRestart = computed(() => {
  const result = setupStore.completionResult as Record<string, unknown> | null
  return result?.needs_restart === true
})

const redirectUrl = computed(() => {
  const result = setupStore.completionResult as Record<string, unknown> | null
  return (result?.redirect_url as string) || ''
})

const isSelfSigned = computed(() => setupStore.wizardData.ssl_type === 'self-signed')

async function complete() {
  await setupStore.completeSetup()
}

async function restartServer() {
  restarting.value = true
  restartError.value = ''
  restartReady.value = false
  try {
    await setupApi.restart()

    // Give the server time to shut down and restart
    countdown.value = 8
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
        restartReady.value = true
        restarting.value = false

        // For non-self-signed certs (Let's Encrypt, custom), try auto-redirect
        if (!isSelfSigned.value && redirectUrl.value) {
          window.location.href = redirectUrl.value + '/login'
        }
      }
    }, 1000)
  } catch {
    restartError.value = 'Could not trigger automatic restart. Please restart the server manually and navigate to ' + redirectUrl.value
    restarting.value = false
  }
}

function openHttpsUrl() {
  if (redirectUrl.value) {
    window.location.href = redirectUrl.value + '/login'
  }
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
      <AppAlert
        type="success"
        title="Setup Complete!"
        :message="needsRestart
          ? 'HTTPS has been configured. Restart the server below to enable it, then sign in.'
          : 'Click &quot;Go to Dashboard&quot; below to get started.'"
      />

      <div v-if="(setupStore.completionResult as Record<string, unknown>)?.encryption_key" class="p-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
        <p class="text-sm font-medium text-yellow-800 dark:text-yellow-200">Save this encryption key now:</p>
        <code class="block mt-2 text-sm font-mono break-all select-all">{{ (setupStore.completionResult as Record<string, unknown>).encryption_key }}</code>
      </div>

      <!-- HTTPS restart section -->
      <div v-if="needsRestart" class="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg space-y-3">
        <p class="text-sm text-blue-800 dark:text-blue-200">
          HTTPS will be available at: <strong>{{ redirectUrl }}</strong>
        </p>

        <!-- Restarting with countdown -->
        <div v-if="restarting" class="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
          <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Restarting server... {{ countdown > 0 ? `ready in ~${countdown}s` : '' }}
        </div>

        <!-- Server ready — self-signed: show manual link + instructions -->
        <div v-else-if="restartReady && isSelfSigned" class="space-y-2">
          <p class="text-sm text-blue-800 dark:text-blue-200">
            Server has restarted. Because you are using a <strong>self-signed certificate</strong>,
            your browser will show a security warning. Click "Advanced" and then "Proceed" to continue.
          </p>
          <AppButton variant="primary" size="sm" @click="openHttpsUrl">
            Open HTTPS Dashboard
          </AppButton>
        </div>

        <!-- Server ready — trusted cert: auto-redirected (fallback link) -->
        <div v-else-if="restartReady" class="space-y-2">
          <p class="text-sm text-blue-800 dark:text-blue-200">
            Redirecting to HTTPS...
          </p>
          <AppButton variant="secondary" size="sm" @click="openHttpsUrl">
            Click here if not redirected
          </AppButton>
        </div>

        <!-- Initial state: show restart button -->
        <AppButton v-else variant="primary" size="sm" @click="restartServer">
          Restart Server for HTTPS
        </AppButton>
        <AppAlert v-if="restartError" type="warning" :message="restartError" />
      </div>
    </div>

    <AppButton v-if="!setupStore.completionResult" variant="primary" size="lg" :loading="setupStore.loading" @click="complete">
      Complete Setup
    </AppButton>
  </div>
</template>
