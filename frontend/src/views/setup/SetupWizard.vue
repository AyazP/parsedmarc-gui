<script setup lang="ts">
import { computed } from 'vue'
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

const steps = [
  { num: 1, label: 'Encryption', component: WelcomeStep },
  { num: 2, label: 'Admin', component: AdminCredentialsStep },
  { num: 3, label: 'SSL/TLS', component: SSLStep },
  { num: 4, label: 'Server', component: ServerStep },
  { num: 5, label: 'Database', component: DatabaseStep },
  { num: 6, label: 'Review', component: ReviewStep },
]

const currentStepComponent = computed(() => steps[setupStore.currentStep - 1]?.component)

function goToDashboard() {
  router.push('/')
}
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
    <!-- Step progress -->
    <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
      <div class="flex items-center justify-between">
        <div v-for="step in steps" :key="step.num" class="flex items-center" :class="step.num < steps.length ? 'flex-1' : ''">
          <div class="flex items-center gap-2">
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
            <span class="text-sm font-medium hidden sm:inline" :class="setupStore.currentStep === step.num ? 'text-primary-700 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'">{{ step.label }}</span>
          </div>
          <div v-if="step.num < steps.length" class="flex-1 mx-4 h-px bg-gray-300 dark:bg-gray-600" />
        </div>
      </div>
    </div>

    <!-- Step content -->
    <div class="p-6">
      <component :is="currentStepComponent" />
    </div>

    <!-- Navigation -->
    <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex justify-between">
      <AppButton v-if="setupStore.currentStep > 1 && !setupStore.completionResult" variant="secondary" @click="setupStore.prevStep()">
        Previous
      </AppButton>
      <div v-else />

      <AppButton v-if="setupStore.currentStep < setupStore.totalSteps && !setupStore.completionResult" @click="setupStore.nextStep()">
        Next
      </AppButton>

      <AppButton v-if="setupStore.completionResult" @click="goToDashboard">
        Go to Dashboard
      </AppButton>
    </div>
  </div>
</template>
