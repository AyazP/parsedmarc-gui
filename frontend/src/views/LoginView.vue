<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PasswordInput from '@/components/forms/PasswordInput.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    const success = await authStore.login(username.value, password.value)
    if (success) {
      const redirect = (route.query.redirect as string) || '/'
      router.push(redirect)
    } else {
      errorMessage.value = authStore.error || 'Invalid username or password'
    }
  } catch {
    errorMessage.value = 'An unexpected error occurred'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm mx-auto">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 text-center mb-6">
        Sign in to ParseDMARC
      </h2>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Error message -->
        <div
          v-if="errorMessage"
          class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-400"
        >
          {{ errorMessage }}
        </div>

        <!-- Username -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Username
          </label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            required
            :disabled="submitting"
            class="block w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 dark:disabled:bg-gray-700"
            placeholder="admin"
          />
        </div>

        <!-- Password -->
        <PasswordInput
          v-model="password"
          label="Password"
          placeholder="Enter your password"
          :disabled="submitting"
        />

        <!-- Submit -->
        <button
          type="submit"
          :disabled="submitting || !username || !password"
          class="w-full rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="submitting" class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Signing in...
          </span>
          <span v-else>Sign in</span>
        </button>
      </form>
    </div>
  </div>
</template>
