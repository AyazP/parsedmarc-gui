<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSetupStore } from '@/stores/setup'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'

const setupStore = useSetupStore()

const host = ref(setupStore.wizardData.host || '0.0.0.0')
const port = ref(String(setupStore.wizardData.port || 8000))
const corsOrigins = ref(setupStore.wizardData.cors_origins || 'http://localhost:3000,http://localhost:8000')
const logLevel = ref(setupStore.wizardData.log_level || 'INFO')

const logLevelOptions = [
  { value: 'DEBUG', label: 'DEBUG' },
  { value: 'INFO', label: 'INFO' },
  { value: 'WARNING', label: 'WARNING' },
  { value: 'ERROR', label: 'ERROR' },
  { value: 'CRITICAL', label: 'CRITICAL' },
]

watch([host, port, corsOrigins, logLevel], () => {
  setupStore.updateWizardData({
    host: host.value,
    port: parseInt(port.value) || 8000,
    cors_origins: corsOrigins.value,
    log_level: logLevel.value,
  })
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900">Server Configuration</h2>
      <p class="mt-2 text-sm text-gray-600">Configure how the application server listens for connections.</p>
    </div>

    <div class="space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <AppInput v-model="host" label="Host" placeholder="0.0.0.0" help-text="0.0.0.0 listens on all interfaces" />
        <AppInput v-model="port" label="Port" type="number" placeholder="8000" />
      </div>
      <AppInput v-model="corsOrigins" label="CORS Origins" placeholder="http://localhost:3000" help-text="Comma-separated list of allowed origins" />
      <AppSelect v-model="logLevel" label="Log Level" :options="logLevelOptions" />
    </div>
  </div>
</template>
