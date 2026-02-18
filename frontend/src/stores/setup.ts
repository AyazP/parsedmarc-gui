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
    db_type: 'sqlite',
    db_path: './data/parsedmarc.db',
    ssl_type: 'self-signed',
  })

  const needsSetup = computed(() => status.value === null || !status.value.is_complete)
  const totalSteps = 6

  // Step validation — returns error message or empty string
  function getStepError(step: number): string {
    const d = wizardData.value
    switch (step) {
      case 1: // Encryption — always valid (auto-generates if not set)
        return ''
      case 2: { // Admin credentials
        if (!d.admin_username || d.admin_username.length < 3)
          return 'Username must be at least 3 characters.'
        if (!d.admin_password || d.admin_password.length < 8)
          return 'Password must be at least 8 characters.'
        return ''
      }
      case 3: { // SSL
        if (d.ssl_type === 'letsencrypt') {
          if (!d.ssl_domain) return 'Domain is required for Let\'s Encrypt.'
          if (!d.ssl_email) return 'Email is required for Let\'s Encrypt.'
        }
        return ''
      }
      case 4: { // Server
        if (!d.host) return 'Host is required.'
        if (!d.port || d.port < 1 || d.port > 65535) return 'Port must be between 1 and 65535.'
        return ''
      }
      case 5: { // Database
        const dbType = d.db_type || 'sqlite'
        if (dbType === 'sqlite') {
          if (!d.db_path) return 'Database path is required.'
        } else {
          if (!d.db_host) return 'Database host is required.'
          if (!d.db_name) return 'Database name is required.'
          if (!d.db_user) return 'Database username is required.'
        }
        return ''
      }
      case 6: // Review — always valid
        return ''
      default:
        return ''
    }
  }

  const isCurrentStepValid = computed(() => getStepError(currentStep.value) === '')
  const currentStepError = computed(() => getStepError(currentStep.value))

  async function fetchStatus() {
    try {
      status.value = await setupApi.getStatus()
    } catch {
      status.value = null
    }
  }

  function nextStep(): boolean {
    const err = getStepError(currentStep.value)
    if (err) return false
    if (currentStep.value < totalSteps) currentStep.value++
    return true
  }

  function prevStep() {
    if (currentStep.value > 1) currentStep.value--
  }

  function goToStep(step: number) {
    if (step >= 1 && step <= totalSteps) currentStep.value = step
  }

  function updateWizardData(data: Partial<CompleteSetupRequest>) {
    // Only merge known keys to prevent prototype pollution
    const safe = Object.fromEntries(
      Object.entries(data).filter(([k]) => !['__proto__', 'constructor', 'prototype'].includes(k))
    )
    Object.assign(wizardData.value, safe)
  }

  async function completeSetup() {
    loading.value = true
    error.value = null
    try {
      const result = await setupApi.complete(wizardData.value as CompleteSetupRequest)
      completionResult.value = result.data ?? null
      if (result.success) {
        // Clear sensitive fields from reactive state after successful submission
        wizardData.value.admin_password = ''
        wizardData.value.encryption_key = ''
        wizardData.value.db_password = ''
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
    isCurrentStepValid,
    currentStepError,
    fetchStatus,
    nextStep,
    prevStep,
    goToStep,
    getStepError,
    updateWizardData,
    completeSetup,
  }
})
