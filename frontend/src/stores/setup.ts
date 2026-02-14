import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setupApi } from '@/api/setup'
import type { SetupStatus, CompleteSetupRequest } from '@/types/setup'

export const useSetupStore = defineStore('setup', () => {
  const status = ref<SetupStatus | null>(null)
  const currentStep = ref(1)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const completionResult = ref<Record<string, unknown> | null>(null)

  const wizardData = ref<Partial<CompleteSetupRequest>>({
    host: '0.0.0.0',
    port: 8000,
    cors_origins: 'http://localhost:3000,http://localhost:8000',
    log_level: 'INFO',
    db_path: './data/parsedmarc.db',
    ssl_type: 'self-signed',
  })

  const needsSetup = computed(() => status.value === null || !status.value.is_complete)
  const totalSteps = 6

  async function fetchStatus() {
    try {
      status.value = await setupApi.getStatus()
    } catch {
      status.value = null
    }
  }

  function nextStep() {
    if (currentStep.value < totalSteps) currentStep.value++
  }

  function prevStep() {
    if (currentStep.value > 1) currentStep.value--
  }

  function goToStep(step: number) {
    if (step >= 1 && step <= totalSteps) currentStep.value = step
  }

  function updateWizardData(data: Partial<CompleteSetupRequest>) {
    Object.assign(wizardData.value, data)
  }

  async function completeSetup() {
    loading.value = true
    error.value = null
    try {
      const result = await setupApi.complete(wizardData.value as CompleteSetupRequest)
      completionResult.value = result.data ?? null
      if (result.success) {
        await fetchStatus()
      }
      return result
    } catch (e: unknown) {
      const err = e as { detail?: string; message?: string }
      error.value = err.detail || err.message || 'Setup failed'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    status,
    currentStep,
    loading,
    error,
    wizardData,
    needsSetup,
    totalSteps,
    completionResult,
    fetchStatus,
    nextStep,
    prevStep,
    goToStep,
    updateWizardData,
    completeSetup,
  }
})
