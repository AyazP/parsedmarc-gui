<script setup lang="ts">
import type { WebhookSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<WebhookSettings>({ required: true })

function update<K extends keyof WebhookSettings>(key: K, value: WebhookSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Webhook Settings" description="Configure webhook endpoint details.">
    <AppInput
      label="URL"
      :model-value="model.url"
      placeholder="https://hooks.example.com/dmarc"
      @update:model-value="update('url', $event)"
    />
    <AppInput
      label="Timeout (seconds)"
      type="number"
      :model-value="String(model.timeout)"
      placeholder="30"
      help-text="Request timeout in seconds."
      @update:model-value="update('timeout', Number($event))"
    />
  </FormSection>
</template>
