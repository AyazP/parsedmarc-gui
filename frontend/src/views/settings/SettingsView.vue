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

const toast = useToast()

const loading = ref(true)
const systemInfo = ref<SystemInfo | null>(null)
const certInfo = ref<CertificateInfo | null>(null)
const renewing = ref(false)

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

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Settings</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <template v-else>
      <!-- System Information -->
      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900">System Information</h2>
        </template>
        <div v-if="systemInfo" class="space-y-3">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p class="text-xs text-gray-500">Version</p>
              <p class="text-sm font-medium text-gray-900">{{ systemInfo.version }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500">Database</p>
              <p class="text-sm font-mono text-gray-600 break-all">{{ systemInfo.database }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500">Data Directory</p>
              <p class="text-sm font-mono text-gray-600 break-all">{{ systemInfo.data_directory }}</p>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-500">Unable to load system information.</div>
      </AppCard>

      <!-- SSL Certificate -->
      <AppCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-900">SSL Certificate</h2>
            <AppButton
              v-if="certInfo && !certInfo.error"
              size="sm"
              variant="secondary"
              :loading="renewing"
              @click="handleRenewCertificate"
            >
              Renew Certificate
            </AppButton>
          </div>
        </template>
        <div v-if="certInfo">
          <AppAlert
            v-if="certInfo.error"
            variant="warning"
            :message="certInfo.error"
          />
          <div v-else class="space-y-3">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <p class="text-xs text-gray-500">Type</p>
                <p class="text-sm font-medium text-gray-900">{{ certInfo.type }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Subject</p>
                <p class="text-sm text-gray-900">{{ certInfo.subject ?? '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Issuer</p>
                <p class="text-sm text-gray-900">{{ certInfo.issuer ?? '-' }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Expires</p>
                <p class="text-sm text-gray-900">{{ formatDate(certInfo.expires) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Days Until Expiry</p>
                <div class="flex items-center gap-2">
                  <p class="text-sm font-medium text-gray-900">{{ certInfo.days_until_expiry ?? '-' }}</p>
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
                <p class="text-xs text-gray-500">Self-Signed</p>
                <p class="text-sm text-gray-900">{{ certInfo.is_self_signed ? 'Yes' : 'No' }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-500">No SSL certificate configured.</div>
      </AppCard>
    </template>
  </div>
</template>
