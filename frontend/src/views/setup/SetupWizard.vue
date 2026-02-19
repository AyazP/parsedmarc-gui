<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSetupStore } from '@/stores/setup'
import AppButton from '@/components/ui/AppButton.vue'
import WelcomeStep from './steps/WelcomeStep.vue'
import AdminCredentialsStep from './steps/AdminCredentialsStep.vue'
import SSLStep from './steps/SSLStep.vue'
import ServerStep from './steps/ServerStep.vue'
import DatabaseStep from './steps/DatabaseStep.vue'
import ReviewStep from './steps/ReviewStep.vue'

const setupStore = useSetupStore()
const router = useRouter()
const validationError = ref('')

const steps = [
  { num: 1, label: 'Encryption', component: WelcomeStep },
  { num: 2, label: 'Admin', component: AdminCredentialsStep },
  { num: 3, label: 'SSL/TLS', component: SSLStep },
  { num: 4, label: 'Server', component: ServerStep },
  { num: 5, label: 'Database', component: DatabaseStep },
  { num: 6, label: 'Review', component: ReviewStep },
]

const currentStepComponent = computed(() => steps[setupStore.currentStep - 1]?.component)

function handleNext() {
  const ok = setupStore.nextStep()
  if (!ok) {
    validationError.value = setupStore.currentStepError
  } else {
    validationError.value = ''
  }
}

const needsRestart = computed(() => {
  const result = setupStore.completionResult as Record<string, unknown> | null
  return result?.needs_restart === true
})

function goToDashboard() {
  // User is auto-logged in after setup — go straight to dashboard
  router.push({ name: 'dashboard' })
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
    <!-- Step progress -->
    <div class="px-4 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
      <div class="flex items-center">
        <template v-for="step in steps" :key="step.num">
          <div class="flex items-center gap-2 shrink-0">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors"
              :class="{
                'bg-primary-600 text-white': setupStore.currentStep === step.num,
                'bg-green-500 text-white': setupStore.currentStep > step.num,
                'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300': setupStore.currentStep < step.num,
              }"
            >
              <svg v-if="setupStore.currentStep > step.num" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <span v-else>{{ step.num }}</span>
            </div>
            <span class="text-sm font-medium hidden sm:inline whitespace-nowrap" :class="setupStore.currentStep === step.num ? 'text-primary-700 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'">{{ step.label }}</span>
          </div>
          <div v-if="step.num < steps.length" class="flex-1 mx-3 h-px bg-gray-300 dark:bg-gray-600 min-w-4" />
        </template>
      </div>
    </div>

    <!-- Step content -->
    <div class="p-6">
      <component :is="currentStepComponent" />
    </div>

    <!-- Navigation -->
    <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 space-y-3">
      <p v-if="validationError" class="text-sm text-red-600 dark:text-red-400">{{ validationError }}</p>
      <div class="flex justify-between">
        <AppButton v-if="setupStore.currentStep > 1 && !setupStore.completionResult" variant="secondary" @click="setupStore.prevStep(); validationError = ''">
          Previous
        </AppButton>
        <div v-else />

        <AppButton v-if="setupStore.currentStep < setupStore.totalSteps && !setupStore.completionResult" @click="handleNext">
          Next
        </AppButton>

        <AppButton v-if="setupStore.completionResult && !needsRestart" @click="goToDashboard">
          Go to Dashboard
        </AppButton>
      </div>
    </div>
  </div>
</template>
