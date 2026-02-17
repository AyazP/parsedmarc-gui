<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useSetupStore } from '@/stores/setup'
import AppInput from '@/components/ui/AppInput.vue'

const setupStore = useSetupStore()

const username = ref(setupStore.wizardData.admin_username || '')
const password = ref(setupStore.wizardData.admin_password || '')
const confirmPassword = ref('')

const usernameError = computed(() => {
  if (!username.value) return ''
  if (username.value.length < 3) return 'Username must be at least 3 characters'
  return ''
})

const passwordError = computed(() => {
  if (!password.value) return ''
  if (password.value.length < 8) return 'Password must be at least 8 characters'
  return ''
})

const confirmError = computed(() => {
  if (!confirmPassword.value) return ''
  if (confirmPassword.value !== password.value) return 'Passwords do not match'
  return ''
})

watch([username, password], () => {
  setupStore.updateWizardData({
    admin_username: username.value,
    admin_password: password.value,
  })
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Admin Credentials</h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Set up the administrator account for the web interface.
      </p>
    </div>

    <div class="space-y-4">
      <AppInput v-model="username" label="Username" placeholder="admin" :error="usernameError" />
      <AppInput v-model="password" label="Password" type="password" placeholder="Minimum 8 characters" :error="passwordError" />
      <AppInput v-model="confirmPassword" label="Confirm Password" type="password" placeholder="Re-enter password" :error="confirmError" />
    </div>
  </div>
</template>
