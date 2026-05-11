<script setup lang="ts">
import type { GELFSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<GELFSettings>({ required: true })

function update<K extends keyof GELFSettings>(key: K, value: GELFSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="GELF Settings" description="Configure Graylog Extended Log Format (GELF) server details.">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Server"
        :model-value="model.server"
        placeholder="localhost"
        @update:model-value="update('server', $event)"
      />
      <AppInput
        label="Port"
        type="number"
        :model-value="String(model.port)"
        placeholder="12201"
        @update:model-value="update('port', Number($event))"
      />
    </div>
  </FormSection>
</template>
