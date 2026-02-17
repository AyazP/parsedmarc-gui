<script setup lang="ts">
import type { MaildirSettings } from '@/types/mailbox'
import AppInput from '@/components/ui/AppInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<MaildirSettings>({ required: true })

function update<K extends keyof MaildirSettings>(key: K, value: MaildirSettings[K]) {
  model.value = { ...model.value, [key]: value }
}
</script>

<template>
  <FormSection title="Maildir Settings" description="Configure a local Maildir path to read reports from.">
    <AppInput
      label="Maildir Path"
      :model-value="model.path"
      placeholder="/var/mail/dmarc"
      help-text="Absolute path to the Maildir directory containing DMARC reports."
      @update:model-value="update('path', $event)"
    />
  </FormSection>
</template>
