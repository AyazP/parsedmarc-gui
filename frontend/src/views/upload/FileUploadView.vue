<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useParsingStore } from '@/stores/parsing'
import { useToast } from '@/composables/useToast'
import type { ParseJob } from '@/types/parsing'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import FileDropZone from '@/components/forms/FileDropZone.vue'

const router = useRouter()
const store = useParsingStore()
const toast = useToast()

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadError = ref<string | null>(null)
const result = ref<ParseJob | null>(null)

function handleFileSelected(file: File) {
  selectedFile.value = file
  result.value = null
  uploadError.value = null
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadError.value = null
  result.value = null

  try {
    result.value = await store.uploadFile(selectedFile.value)
    toast.success('File parsed successfully!')
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    uploadError.value = err.detail || err.message || 'Upload failed.'
  } finally {
    uploading.value = false
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function reset() {
  selectedFile.value = null
  result.value = null
  uploadError.value = null
}

const statusVariant: Record<string, 'success' | 'error' | 'info' | 'neutral'> = {
  completed: 'success',
  failed: 'error',
  running: 'info',
  pending: 'neutral',
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Upload Report</h1>

    <AppCard>
      <template #header>
        <h2 class="text-base font-semibold text-gray-900">Upload DMARC Report File</h2>
      </template>
      <div class="space-y-4">
        <FileDropZone
          accept=".xml,.gz,.zip,.eml,.msg"
          :disabled="uploading"
          @file-selected="handleFileSelected"
        />

        <div v-if="selectedFile" class="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
          <div>
            <p class="text-sm font-medium text-gray-900">{{ selectedFile.name }}</p>
            <p class="text-xs text-gray-500">{{ formatBytes(selectedFile.size) }}</p>
          </div>
          <div class="flex items-center gap-2">
            <AppButton size="sm" variant="secondary" :disabled="uploading" @click="reset">Clear</AppButton>
            <AppButton size="sm" :loading="uploading" @click="handleUpload">Upload & Parse</AppButton>
          </div>
        </div>

        <AppAlert v-if="uploadError" variant="error" :message="uploadError" dismissible @dismiss="uploadError = null" />
      </div>
    </AppCard>

    <AppCard v-if="result">
      <template #header>
        <h2 class="text-base font-semibold text-gray-900">Parse Result</h2>
      </template>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span class="text-sm text-gray-600">Status:</span>
          <AppBadge :text="result.status" :variant="statusVariant[result.status] ?? 'neutral'" />
        </div>
        <div v-if="result.error_message" class="text-sm text-red-600">
          {{ result.error_message }}
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-gray-900">{{ result.aggregate_reports_count }}</p>
            <p class="text-xs text-gray-500">Aggregate</p>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-gray-900">{{ result.forensic_reports_count }}</p>
            <p class="text-xs text-gray-500">Forensic</p>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-gray-900">{{ result.smtp_tls_reports_count }}</p>
            <p class="text-xs text-gray-500">SMTP TLS</p>
          </div>
        </div>
        <div class="flex justify-end gap-3">
          <AppButton variant="secondary" @click="router.push('/reports')">View Reports</AppButton>
          <AppButton variant="secondary" @click="reset">Upload Another</AppButton>
        </div>
      </div>
    </AppCard>
  </div>
</template>
