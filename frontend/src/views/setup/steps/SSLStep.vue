<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSetupStore } from '@/stores/setup'
import { setupApi } from '@/api/setup'
import { useToast } from '@/composables/useToast'
import type { SSLType, ChallengeType, DNSProvider, CertificateValidationResult } from '@/types/setup'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const setupStore = useSetupStore()
const toast = useToast()

const sslType = ref<SSLType>(setupStore.wizardData.ssl_type || 'self-signed')
const commonName = ref(setupStore.wizardData.ssl_common_name || 'localhost')
const domain = ref(setupStore.wizardData.ssl_domain || '')
const email = ref(setupStore.wizardData.ssl_email || '')
const staging = ref(setupStore.wizardData.ssl_staging ?? true)

// Challenge type for Let's Encrypt
const challengeType = ref<ChallengeType>(setupStore.wizardData.ssl_challenge_type || 'http-01')
const dnsProvider = ref<DNSProvider>(setupStore.wizardData.ssl_dns_provider || 'cloudflare')
const dnsToken = ref('')
const dnsAccessKeyId = ref('')
const dnsSecretKey = ref('')
const dnsServiceAccountJson = ref('')

// Custom cert upload
const certFile = ref<File | null>(null)
const keyFile = ref<File | null>(null)
const chainFile = ref<File | null>(null)
const validationResult = ref<CertificateValidationResult | null>(null)
const validating = ref(false)
const uploadingCert = ref(false)
const certUploaded = ref(false)

const sslOptions: { value: SSLType; label: string; desc: string }[] = [
  { value: 'self-signed', label: 'Self-Signed', desc: 'Generate a self-signed certificate (development/testing)' },
  { value: 'letsencrypt', label: "Let's Encrypt", desc: 'Free automated certificate (production)' },
  { value: 'custom', label: 'Custom Certificate', desc: 'Upload your own SSL certificate files' },
  { value: 'skip', label: 'Skip SSL', desc: 'Run without HTTPS (not recommended)' },
]

const challengeTypeOptions = [
  { value: 'http-01', label: 'HTTP-01 (Standalone)' },
  { value: 'dns-01', label: 'DNS-01 (DNS Provider)' },
]

const dnsProviderOptions = [
  { value: 'cloudflare', label: 'Cloudflare' },
  { value: 'route53', label: 'AWS Route 53' },
  { value: 'digitalocean', label: 'DigitalOcean' },
  { value: 'google', label: 'Google Cloud DNS' },
]

function buildDnsCredentials(): Record<string, string> {
  switch (dnsProvider.value) {
    case 'cloudflare':
      return { api_token: dnsToken.value }
    case 'route53':
      return { access_key_id: dnsAccessKeyId.value, secret_access_key: dnsSecretKey.value }
    case 'digitalocean':
      return { api_token: dnsToken.value }
    case 'google':
      return { service_account_json: dnsServiceAccountJson.value }
    default:
      return {}
  }
}

watch([sslType, commonName, domain, email, staging, challengeType, dnsProvider], () => {
  setupStore.updateWizardData({
    ssl_type: sslType.value,
    ssl_common_name: commonName.value,
    ssl_domain: domain.value,
    ssl_email: email.value,
    ssl_staging: staging.value,
    ssl_challenge_type: challengeType.value,
    ssl_dns_provider: challengeType.value === 'dns-01' ? dnsProvider.value : undefined,
    ssl_dns_credentials: challengeType.value === 'dns-01' ? buildDnsCredentials() : undefined,
  })
})

watch([dnsToken, dnsAccessKeyId, dnsSecretKey, dnsServiceAccountJson], () => {
  if (challengeType.value === 'dns-01') {
    setupStore.updateWizardData({
      ssl_dns_credentials: buildDnsCredentials(),
    })
  }
})

function onCertFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  certFile.value = input.files?.[0] ?? null
  validationResult.value = null
  certUploaded.value = false
}
function onKeyFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  keyFile.value = input.files?.[0] ?? null
  validationResult.value = null
  certUploaded.value = false
}
function onChainFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  chainFile.value = input.files?.[0] ?? null
  validationResult.value = null
  certUploaded.value = false
}

async function handleValidate() {
  if (!certFile.value || !keyFile.value) {
    toast.error('Certificate and private key files are required.')
    return
  }
  validating.value = true
  validationResult.value = null
  try {
    validationResult.value = await setupApi.validateCertificate({
      certificate: certFile.value,
      private_key: keyFile.value,
      chain: chainFile.value,
    })
    if (validationResult.value.valid) {
      toast.success('Certificate is valid.')
    } else {
      toast.error(validationResult.value.error || 'Validation failed.')
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Validation failed.')
  } finally {
    validating.value = false
  }
}

async function handleUploadCert() {
  if (!certFile.value || !keyFile.value) return
  uploadingCert.value = true
  try {
    const result = await setupApi.uploadCertificate({
      certificate: certFile.value,
      private_key: keyFile.value,
      chain: chainFile.value,
    })
    if (result.success) {
      toast.success('Certificate uploaded successfully.')
      certUploaded.value = true
    } else {
      toast.error(result.message || 'Upload failed.')
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Upload failed.')
  } finally {
    uploadingCert.value = false
  }
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
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

    <!-- Self-signed options -->
    <div v-if="sslType === 'self-signed'" class="space-y-4 pt-2">
      <AppInput v-model="commonName" label="Common Name" placeholder="localhost" help-text="Usually the hostname or domain" />
    </div>

    <!-- Let's Encrypt options -->
    <div v-if="sslType === 'letsencrypt'" class="space-y-4 pt-2">
      <AppSelect
        v-model="challengeType"
        label="Challenge Type"
        :options="challengeTypeOptions"
      />

      <AppAlert
        v-if="challengeType === 'http-01'"
        variant="info"
        message="Your domain must point to this server and port 80 must be accessible. Certbot must be installed."
      />
      <AppAlert
        v-else
        variant="info"
        message="DNS-01 validation does not require port 80. Provide your DNS provider API credentials."
      />

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <AppInput v-model="domain" label="Domain" placeholder="example.com" help-text="Must be publicly accessible" />
        <AppInput v-model="email" label="Email" type="email" placeholder="admin@example.com" />
      </div>

      <!-- DNS-01 provider fields -->
      <template v-if="challengeType === 'dns-01'">
        <AppSelect
          v-model="dnsProvider"
          label="DNS Provider"
          :options="dnsProviderOptions"
        />

        <AppInput
          v-if="dnsProvider === 'cloudflare' || dnsProvider === 'digitalocean'"
          v-model="dnsToken"
          label="API Token"
          type="password"
          :placeholder="dnsProvider === 'cloudflare' ? 'Cloudflare API token' : 'DigitalOcean API token'"
        />

        <template v-if="dnsProvider === 'route53'">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <AppInput
              v-model="dnsAccessKeyId"
              label="AWS Access Key ID"
              type="password"
              placeholder="AKIAIOSFODNN7EXAMPLE"
            />
            <AppInput
              v-model="dnsSecretKey"
              label="AWS Secret Access Key"
              type="password"
              placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            />
          </div>
        </template>

        <div v-if="dnsProvider === 'google'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Service Account JSON</label>
          <textarea
            v-model="dnsServiceAccountJson"
            rows="4"
            placeholder='Paste your Google Cloud service account JSON here...'
            class="block w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 dark:bg-gray-700 dark:placeholder-gray-400"
          />
        </div>
      </template>

      <AppToggle v-model="staging" label="Use staging server (for testing)" />
    </div>

    <!-- Custom Certificate upload -->
    <div v-if="sslType === 'custom'" class="space-y-4 pt-2">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Certificate File (.pem/.crt)</label>
          <input
            type="file"
            accept=".pem,.crt,.cer"
            :disabled="uploadingCert"
            class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300 dark:hover:file:bg-primary-800/40"
            @change="onCertFileChange"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Private Key File (.pem/.key)</label>
          <input
            type="file"
            accept=".pem,.key"
            :disabled="uploadingCert"
            class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300 dark:hover:file:bg-primary-800/40"
            @change="onKeyFileChange"
          />
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Chain File (.pem/.crt) — optional</label>
        <input
          type="file"
          accept=".pem,.crt,.cer"
          :disabled="uploadingCert"
          class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300 dark:hover:file:bg-primary-800/40"
          @change="onChainFileChange"
        />
      </div>

      <!-- Validation result -->
      <AppAlert
        v-if="validationResult && validationResult.valid"
        variant="success"
        :message="`Valid — Subject: ${validationResult.subject}, Issuer: ${validationResult.issuer}, Expires: ${formatDate(validationResult.expires)} (${validationResult.days_until_expiry} days)`"
      />
      <AppAlert
        v-if="validationResult && !validationResult.valid"
        variant="error"
        :message="validationResult.error || 'Validation failed.'"
      />
      <AppAlert
        v-if="validationResult?.warning"
        variant="warning"
        :message="validationResult.warning"
      />
      <AppAlert
        v-if="certUploaded"
        variant="success"
        message="Certificate uploaded and will be applied when setup completes."
      />

      <div class="flex items-center gap-3">
        <AppButton
          size="sm"
          variant="secondary"
          :loading="validating"
          :disabled="!certFile || !keyFile || uploadingCert"
          @click="handleValidate"
        >
          Validate
        </AppButton>
        <AppButton
          size="sm"
          :loading="uploadingCert"
          :disabled="!validationResult?.valid || certUploaded"
          @click="handleUploadCert"
        >
          Upload Certificate
        </AppButton>
      </div>
    </div>
  </div>
</template>
