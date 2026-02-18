<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'
import { setupApi } from '@/api/setup'
import { useToast } from '@/composables/useToast'
import type { SystemInfo } from '@/types/system'
import type { CertificateInfo, CertificateValidationResult, ChallengeType, DNSProvider } from '@/types/setup'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import UpdateSettings from '@/components/updates/UpdateSettings.vue'
import DatabaseSettings from '@/components/settings/DatabaseSettings.vue'

const toast = useToast()

const loading = ref(true)
const systemInfo = ref<SystemInfo | null>(null)
const certInfo = ref<CertificateInfo | null>(null)
const renewing = ref(false)

// Let's Encrypt upgrade form
const showUpgradeForm = ref(false)
const upgrading = ref(false)
const upgradeDomain = ref('')
const upgradeEmail = ref('')
const upgradeStaging = ref(false)
const upgradeChallengeType = ref<ChallengeType>('http-01')
const upgradeDnsProvider = ref<DNSProvider>('cloudflare')
const upgradeDnsToken = ref('')
const upgradeDnsAccessKeyId = ref('')
const upgradeDnsSecretKey = ref('')
const upgradeDnsServiceAccountJson = ref('')

// Custom certificate upload form
const showUploadForm = ref(false)
const uploadCertFile = ref<File | null>(null)
const uploadKeyFile = ref<File | null>(null)
const uploadChainFile = ref<File | null>(null)
const uploadValidation = ref<CertificateValidationResult | null>(null)
const validatingUpload = ref(false)
const uploading = ref(false)

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

onMounted(async () => {
  try {
    const [sys, cert] = await Promise.all([
      systemApi.systemInfo(),
      setupApi.getCertificate().catch(() => null),
    ])
    systemInfo.value = sys
    certInfo.value = cert
  } catch {
    toast.error('Failed to load system information.')
  } finally {
    loading.value = false
  }
})

async function handleRenewCertificate() {
  renewing.value = true
  try {
    const result = await setupApi.renewCertificate()
    if (result.success) {
      toast.success('Certificate renewed successfully.')
      certInfo.value = await setupApi.getCertificate()
    } else {
      toast.error(result.message || 'Certificate renewal failed.')
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Certificate renewal failed.')
  } finally {
    renewing.value = false
  }
}

function buildDnsCredentials(): Record<string, string> {
  switch (upgradeDnsProvider.value) {
    case 'cloudflare':
      return { api_token: upgradeDnsToken.value }
    case 'route53':
      return { access_key_id: upgradeDnsAccessKeyId.value, secret_access_key: upgradeDnsSecretKey.value }
    case 'digitalocean':
      return { api_token: upgradeDnsToken.value }
    case 'google':
      return { service_account_json: upgradeDnsServiceAccountJson.value }
    default:
      return {}
  }
}

async function handleUpgradeCertificate() {
  if (!upgradeDomain.value || !upgradeEmail.value) {
    toast.error('Domain and email are required.')
    return
  }
  upgrading.value = true
  try {
    const result = await setupApi.setSSL({
      type: 'letsencrypt',
      domain: upgradeDomain.value,
      email: upgradeEmail.value,
      staging: upgradeStaging.value,
      challenge_type: upgradeChallengeType.value,
      dns_provider: upgradeChallengeType.value === 'dns-01' ? upgradeDnsProvider.value : undefined,
      dns_credentials: upgradeChallengeType.value === 'dns-01' ? buildDnsCredentials() : undefined,
    })
    if (result.success) {
      toast.success('Let\'s Encrypt certificate obtained! Restart the application to use it.')
      certInfo.value = await setupApi.getCertificate()
      cancelUpgrade()
    } else {
      toast.error(result.message || 'Certificate request failed.')
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Certificate request failed.')
  } finally {
    upgrading.value = false
  }
}

function cancelUpgrade() {
  showUpgradeForm.value = false
  upgradeDomain.value = ''
  upgradeEmail.value = ''
  upgradeStaging.value = false
  upgradeChallengeType.value = 'http-01'
  upgradeDnsProvider.value = 'cloudflare'
  upgradeDnsToken.value = ''
  upgradeDnsAccessKeyId.value = ''
  upgradeDnsSecretKey.value = ''
  upgradeDnsServiceAccountJson.value = ''
}

function onCertFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  uploadCertFile.value = input.files?.[0] ?? null
  uploadValidation.value = null
}
function onKeyFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  uploadKeyFile.value = input.files?.[0] ?? null
  uploadValidation.value = null
}
function onChainFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  uploadChainFile.value = input.files?.[0] ?? null
  uploadValidation.value = null
}

async function handleValidateUpload() {
  if (!uploadCertFile.value || !uploadKeyFile.value) {
    toast.error('Certificate and private key files are required.')
    return
  }
  validatingUpload.value = true
  uploadValidation.value = null
  try {
    uploadValidation.value = await setupApi.validateCertificate({
      certificate: uploadCertFile.value,
      private_key: uploadKeyFile.value,
      chain: uploadChainFile.value,
    })
    if (uploadValidation.value.valid) {
      toast.success('Certificate is valid.')
    } else {
      toast.error(uploadValidation.value.error || 'Validation failed.')
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Validation failed.')
  } finally {
    validatingUpload.value = false
  }
}

async function handleUploadCertificate() {
  if (!uploadCertFile.value || !uploadKeyFile.value) return
  uploading.value = true
  try {
    const result = await setupApi.uploadCertificate({
      certificate: uploadCertFile.value,
      private_key: uploadKeyFile.value,
      chain: uploadChainFile.value,
    })
    if (result.success) {
      toast.success('Certificate uploaded! Restart the application to apply.')
      certInfo.value = await setupApi.getCertificate()
      cancelUpload()
    } else {
      toast.error(result.message || 'Upload failed.')
    }
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    toast.error(err.detail || err.message || 'Upload failed.')
  } finally {
    uploading.value = false
  }
}

function cancelUpload() {
  showUploadForm.value = false
  uploadCertFile.value = null
  uploadKeyFile.value = null
  uploadChainFile.value = null
  uploadValidation.value = null
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <template v-else>
      <!-- System Information -->
      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">System Information</h2>
        </template>
        <div v-if="systemInfo">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Version</p>
              <p class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ systemInfo.version }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Database</p>
              <p class="mt-1 text-sm font-mono text-gray-700 dark:text-gray-300 break-all">{{ systemInfo.database }}</p>
            </div>
            <div>
              <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Data Directory</p>
              <p class="mt-1 text-sm font-mono text-gray-700 dark:text-gray-300 break-all">{{ systemInfo.data_directory }}</p>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-500 dark:text-gray-400">Unable to load system information.</div>
      </AppCard>

      <!-- Database -->
      <DatabaseSettings />

      <!-- Update Checker -->
      <UpdateSettings />

      <!-- SSL Certificate -->
      <AppCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">SSL Certificate</h2>
            <div class="flex items-center gap-2">
              <AppButton
                v-if="certInfo && !certInfo.error"
                size="sm"
                variant="secondary"
                :disabled="showUploadForm || showUpgradeForm"
                @click="showUploadForm = true"
              >
                Upload Custom
              </AppButton>
              <AppButton
                v-if="certInfo && !certInfo.error && (certInfo.is_self_signed || certInfo.type === 'custom')"
                size="sm"
                variant="secondary"
                :disabled="showUpgradeForm || showUploadForm"
                @click="showUpgradeForm = true"
              >
                Upgrade to Let's Encrypt
              </AppButton>
              <AppButton
                v-if="certInfo && !certInfo.error && certInfo.type === 'letsencrypt'"
                size="sm"
                variant="secondary"
                :loading="renewing"
                @click="handleRenewCertificate"
              >
                Renew Certificate
              </AppButton>
            </div>
          </div>
        </template>
        <div v-if="certInfo">
          <AppAlert
            v-if="certInfo.error"
            variant="warning"
            :message="certInfo.error"
          />
          <div v-else class="space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</p>
                <p class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ certInfo.type }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Subject</p>
                <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 break-all">{{ certInfo.subject ?? '-' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Issuer</p>
                <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 break-all">{{ certInfo.issuer ?? '-' }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Expires</p>
                <p class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ formatDate(certInfo.expires) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Days Until Expiry</p>
                <div class="mt-1 flex items-center gap-2">
                  <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ certInfo.days_until_expiry ?? '-' }}</p>
                  <AppBadge
                    v-if="certInfo.is_expired"
                    text="Expired"
                    variant="error"
                  />
                  <AppBadge
                    v-else-if="certInfo.days_until_expiry !== undefined && certInfo.days_until_expiry < 30"
                    text="Expiring Soon"
                    variant="warning"
                  />
                  <AppBadge
                    v-else
                    text="Valid"
                    variant="success"
                  />
                </div>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Self-Signed</p>
                <p class="mt-1 text-sm font-semibold text-gray-900 dark:text-gray-100">{{ certInfo.is_self_signed ? 'Yes' : 'No' }}</p>
              </div>
            </div>

            <!-- Upload Custom Certificate form -->
            <div v-if="showUploadForm" class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Upload Custom Certificate</h3>
              <AppAlert
                variant="info"
                message="Upload your PEM-encoded certificate and private key files. The certificate will be validated before applying."
              />
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Certificate File (.pem/.crt)</label>
                  <input
                    type="file"
                    accept=".pem,.crt,.cer"
                    :disabled="uploading"
                    class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300 dark:hover:file:bg-primary-800/40"
                    @change="onCertFileChange"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Private Key File (.pem/.key)</label>
                  <input
                    type="file"
                    accept=".pem,.key"
                    :disabled="uploading"
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
                  :disabled="uploading"
                  class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300 dark:hover:file:bg-primary-800/40"
                  @change="onChainFileChange"
                />
              </div>

              <!-- Validation result -->
              <AppAlert
                v-if="uploadValidation && uploadValidation.valid"
                variant="success"
                :message="`Valid — Subject: ${uploadValidation.subject}, Issuer: ${uploadValidation.issuer}, Expires: ${formatDate(uploadValidation.expires)} (${uploadValidation.days_until_expiry} days)`"
              />
              <AppAlert
                v-if="uploadValidation && !uploadValidation.valid"
                variant="error"
                :message="uploadValidation.error || 'Validation failed.'"
              />
              <AppAlert
                v-if="uploadValidation?.warning"
                variant="warning"
                :message="uploadValidation.warning"
              />

              <div class="flex items-center gap-3">
                <AppButton
                  size="sm"
                  variant="secondary"
                  :loading="validatingUpload"
                  :disabled="!uploadCertFile || !uploadKeyFile || uploading"
                  @click="handleValidateUpload"
                >
                  Validate
                </AppButton>
                <AppButton
                  size="sm"
                  :loading="uploading"
                  :disabled="!uploadValidation?.valid"
                  @click="handleUploadCertificate"
                >
                  Apply Certificate
                </AppButton>
                <AppButton
                  size="sm"
                  variant="ghost"
                  :disabled="uploading"
                  @click="cancelUpload"
                >
                  Cancel
                </AppButton>
              </div>
            </div>

            <!-- Upgrade to Let's Encrypt form -->
            <div v-if="showUpgradeForm" class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Upgrade to Let's Encrypt</h3>

              <!-- Challenge type selection -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <AppSelect
                  v-model="upgradeChallengeType"
                  label="Challenge Type"
                  :options="challengeTypeOptions"
                  :disabled="upgrading"
                />
              </div>

              <AppAlert
                v-if="upgradeChallengeType === 'http-01'"
                variant="info"
                message="Your domain must point to this server and port 80 must be accessible. Certbot must be installed on the server."
              />
              <AppAlert
                v-else
                variant="info"
                message="DNS-01 validation does not require port 80. Your DNS provider API credentials are needed to create the verification record."
              />

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <AppInput
                  v-model="upgradeDomain"
                  label="Domain"
                  placeholder="e.g. dmarc.example.com"
                  :disabled="upgrading"
                />
                <AppInput
                  v-model="upgradeEmail"
                  label="Email"
                  placeholder="admin@example.com"
                  :disabled="upgrading"
                />
              </div>

              <!-- DNS-01 provider fields -->
              <template v-if="upgradeChallengeType === 'dns-01'">
                <AppSelect
                  v-model="upgradeDnsProvider"
                  label="DNS Provider"
                  :options="dnsProviderOptions"
                  :disabled="upgrading"
                />

                <!-- Cloudflare / DigitalOcean: single token -->
                <AppInput
                  v-if="upgradeDnsProvider === 'cloudflare' || upgradeDnsProvider === 'digitalocean'"
                  v-model="upgradeDnsToken"
                  label="API Token"
                  type="password"
                  :placeholder="upgradeDnsProvider === 'cloudflare' ? 'Cloudflare API token' : 'DigitalOcean API token'"
                  :disabled="upgrading"
                />

                <!-- Route53: two fields -->
                <template v-if="upgradeDnsProvider === 'route53'">
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <AppInput
                      v-model="upgradeDnsAccessKeyId"
                      label="AWS Access Key ID"
                      type="password"
                      placeholder="AKIAIOSFODNN7EXAMPLE"
                      :disabled="upgrading"
                    />
                    <AppInput
                      v-model="upgradeDnsSecretKey"
                      label="AWS Secret Access Key"
                      type="password"
                      placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                      :disabled="upgrading"
                    />
                  </div>
                </template>

                <!-- Google Cloud DNS: JSON textarea -->
                <div v-if="upgradeDnsProvider === 'google'">
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Service Account JSON</label>
                  <textarea
                    v-model="upgradeDnsServiceAccountJson"
                    :disabled="upgrading"
                    rows="4"
                    placeholder='Paste your Google Cloud service account JSON here...'
                    class="block w-full rounded-lg border px-3 py-2 text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 dark:bg-gray-700 dark:placeholder-gray-400 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500 dark:disabled:text-gray-500"
                  />
                </div>
              </template>

              <AppToggle
                v-model="upgradeStaging"
                label="Use staging server (for testing)"
                :disabled="upgrading"
              />
              <div class="flex items-center gap-3">
                <AppButton
                  size="sm"
                  :loading="upgrading"
                  @click="handleUpgradeCertificate"
                >
                  Request Certificate
                </AppButton>
                <AppButton
                  size="sm"
                  variant="secondary"
                  :disabled="upgrading"
                  @click="cancelUpgrade"
                >
                  Cancel
                </AppButton>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-500 dark:text-gray-400">No SSL certificate configured.</div>
      </AppCard>
    </template>
  </div>
</template>
