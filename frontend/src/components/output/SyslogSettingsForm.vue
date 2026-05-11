<script setup lang="ts">
import type { SyslogSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<SyslogSettings>({ required: true })

function update<K extends keyof SyslogSettings>(key: K, value: SyslogSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Syslog Settings" description="Configure syslog server connection details.">
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
        placeholder="514"
        @update:model-value="update('port', Number($event))"
      />
    </div>
  </FormSection>
</template>
