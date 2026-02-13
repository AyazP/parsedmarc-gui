<script setup lang="ts">
import { ref } from 'vue'
import { useSetupStore } from '@/stores/setup'
import { setupApi } from '@/api/setup'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const setupStore = useSetupStore()
const generatedKey = ref('')
const customKey = ref('')
const useCustom = ref(false)
const generating = ref(false)
const error = ref('')

async function generateKey() {
  generating.value = true
  error.value = ''
  try {
    const result = await setupApi.generateEncryptionKey()
    generatedKey.value = result.encryption_key
    setupStore.updateWizardData({ encryption_key: result.encryption_key })
  } catch (e: unknown) {
    error.value = (e as { detail?: string }).detail || 'Failed to generate key'
  } finally {
    generating.value = false
  }
}

function useCustomKey() {
  if (customKey.value.length >= 32) {
    setupStore.updateWizardData({ encryption_key: customKey.value })
    generatedKey.value = ''
  }
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(generatedKey.value)
  } catch {
    // Clipboard API not available
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-gray-900">Welcome to ParseDMARC</h2>
      <p class="mt-2 text-sm text-gray-600">
        Let's set up your DMARC report parser. First, we need to configure an encryption key
        that will be used to securely store your credentials.
      </p>
    </div>

    <AppAlert type="warning" title="Important" message="Save the encryption key securely. If lost, encrypted credentials cannot be recovered." />

    <div class="space-y-4">
      <AppButton :loading="generating" @click="generateKey">
        Generate Encryption Key
      </AppButton>

      <div v-if="generatedKey" class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Generated Key</label>
        <div class="flex gap-2">
          <code class="flex-1 block bg-gray-100 rounded-lg px-3 py-2 text-sm font-mono break-all select-all">{{ generatedKey }}</code>
          <AppButton variant="secondary" size="sm" @click="copyToClipboard">Copy</AppButton>
        </div>
      </div>

      <div class="relative">
        <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-300" /></div>
        <div class="relative flex justify-center text-sm"><span class="bg-white px-2 text-gray-500">or</span></div>
      </div>

      <div>
        <button class="text-sm text-primary-600 hover:text-primary-700" @click="useCustom = !useCustom">
          {{ useCustom ? 'Hide' : 'Paste your own key' }}
        </button>
        <div v-if="useCustom" class="mt-2 space-y-2">
          <AppInput
            v-model="customKey"
            label="Custom Encryption Key"
            placeholder="Base64-encoded Fernet key (min 32 chars)"
          />
          <AppButton variant="secondary" size="sm" :disabled="customKey.length < 32" @click="useCustomKey">
            Use This Key
          </AppButton>
        </div>
      </div>
    </div>

    <AppAlert v-if="error" type="error" :message="error" />
  </div>
</template>
