<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'
import { setupApi } from '@/api/setup'
import { useToast } from '@/composables/useToast'
import type { SystemInfo } from '@/types/system'
import type { CertificateInfo } from '@/types/setup'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import UpdateSettings from '@/components/updates/UpdateSettings.vue'

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
    })
    if (result.success) {
      toast.success('Let\'s Encrypt certificate obtained! Restart the application to use it.')
      certInfo.value = await setupApi.getCertificate()
      showUpgradeForm.value = false
      upgradeDomain.value = ''
      upgradeEmail.value = ''
      upgradeStaging.value = false
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
        <div v-if="systemInfo" class="space-y-3">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">Version</p>
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ systemInfo.version }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">Database</p>
              <p class="text-sm font-mono text-gray-600 dark:text-gray-400 break-all">{{ systemInfo.database }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400">Data Directory</p>
              <p class="text-sm font-mono text-gray-600 dark:text-gray-400 break-all">{{ systemInfo.data_directory }}</p>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-500 dark:text-gray-400">Unable to load system information.</div>
      </AppCard>

      <!-- Update Checker -->
      <UpdateSettings />

      <!-- SSL Certificate -->
      <AppCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">SSL Certificate</h2>
            <div class="flex items-center gap-2">
              <AppButton
                v-if="certInfo && !certInfo.error && certInfo.is_self_signed"
                size="sm"
                variant="ghost"
                :disabled="showUpgradeForm"
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
                <p class="text-xs text-gray-500 dark:text-gray-400">Type</p>
                <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ certInfo.type }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">Subject</p>
                <p class="text-sm text-gray-900 dark:text-gray-100">{{ certInfo.subject ?? '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">Issuer</p>
                <p class="text-sm text-gray-900 dark:text-gray-100">{{ certInfo.issuer ?? '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">Expires</p>
                <p class="text-sm text-gray-900 dark:text-gray-100">{{ formatDate(certInfo.expires) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">Days Until Expiry</p>
                <div class="flex items-center gap-2">
                  <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ certInfo.days_until_expiry ?? '-' }}</p>
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
                <p class="text-xs text-gray-500 dark:text-gray-400">Self-Signed</p>
                <p class="text-sm text-gray-900 dark:text-gray-100">{{ certInfo.is_self_signed ? 'Yes' : 'No' }}</p>
              </div>
            </div>

            <!-- Upgrade to Let's Encrypt form -->
            <div v-if="showUpgradeForm" class="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Upgrade to Let's Encrypt</h3>
              <AppAlert
                variant="info"
                message="Your domain must point to this server and port 80 must be accessible for Let's Encrypt verification. Certbot must be installed on the server."
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
