<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSetupStore } from '@/stores/setup'
import type { SSLType } from '@/types/setup'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'

const setupStore = useSetupStore()

const sslType = ref<SSLType>(setupStore.wizardData.ssl_type || 'self-signed')
const commonName = ref(setupStore.wizardData.ssl_common_name || 'localhost')
const domain = ref(setupStore.wizardData.ssl_domain || '')
const email = ref(setupStore.wizardData.ssl_email || '')
const staging = ref(setupStore.wizardData.ssl_staging ?? true)
const certPath = ref(setupStore.wizardData.ssl_certificate_path || '')
const keyPath = ref(setupStore.wizardData.ssl_private_key_path || '')

const sslOptions: { value: SSLType; label: string; desc: string }[] = [
  { value: 'self-signed', label: 'Self-Signed', desc: 'Generate a self-signed certificate (development/testing)' },
  { value: 'letsencrypt', label: "Let's Encrypt", desc: 'Free automated certificate (production)' },
  { value: 'custom', label: 'Custom Certificate', desc: 'Use your own SSL certificate files' },
  { value: 'skip', label: 'Skip SSL', desc: 'Run without HTTPS (not recommended)' },
]

watch([sslType, commonName, domain, email, staging, certPath, keyPath], () => {
  setupStore.updateWizardData({
    ssl_type: sslType.value,
    ssl_common_name: commonName.value,
    ssl_domain: domain.value,
    ssl_email: email.value,
    ssl_staging: staging.value,
    ssl_certificate_path: certPath.value,
    ssl_private_key_path: keyPath.value,
  })
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">SSL/TLS Configuration</h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">Choose how to secure your connection with HTTPS.</p>
    </div>

    <div class="space-y-3">
      <div
        v-for="opt in sslOptions"
        :key="opt.value"
        class="relative flex items-start p-4 border rounded-lg cursor-pointer transition-colors"
        :class="sslType === opt.value ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
        @click="sslType = opt.value"
      >
        <input type="radio" :checked="sslType === opt.value" class="mt-0.5 h-4 w-4 text-primary-600" />
        <div class="ml-3">
          <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ opt.label }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ opt.desc }}</p>
        </div>
      </div>
    </div>

    <div v-if="sslType === 'self-signed'" class="space-y-4 pt-2">
      <AppInput v-model="commonName" label="Common Name" placeholder="localhost" help-text="Usually the hostname or domain" />
    </div>

    <div v-if="sslType === 'letsencrypt'" class="space-y-4 pt-2">
      <AppInput v-model="domain" label="Domain" placeholder="example.com" help-text="Must be publicly accessible" />
      <AppInput v-model="email" label="Email" type="email" placeholder="admin@example.com" />
      <AppToggle v-model="staging" label="Use staging server (for testing)" />
    </div>

    <div v-if="sslType === 'custom'" class="space-y-4 pt-2">
      <AppInput v-model="certPath" label="Certificate Path" placeholder="/path/to/cert.pem" />
      <AppInput v-model="keyPath" label="Private Key Path" placeholder="/path/to/key.pem" />
    </div>
  </div>
</template>
