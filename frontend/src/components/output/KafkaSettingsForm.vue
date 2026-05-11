<script setup lang="ts">
import type { KafkaSettings } from '@/types/output'
import AppInput from '@/components/ui/AppInput.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import PasswordInput from '@/components/forms/PasswordInput.vue'
import FormSection from '@/components/forms/FormSection.vue'

const model = defineModel<KafkaSettings>({ required: true })

function update<K extends keyof KafkaSettings>(key: K, value: KafkaSettings[K]) {
  model.value = { ...model.value, [key]: value }
}

function serversFromString(val: string): string[] {
  return val.split(',').map(s => s.trim()).filter(Boolean)
}
</script>

<template>
  <FormSection title="Kafka Settings" description="Configure Apache Kafka connection details.">
    <AppInput
      label="Bootstrap Servers"
      :model-value="model.servers.join(', ')"
      placeholder="localhost:9092"
      help-text="Comma-separated list of Kafka bootstrap servers."
      @update:model-value="update('servers', serversFromString($event))"
    />
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <AppInput
        label="Aggregate Topic"
        :model-value="model.aggregate_topic"
        placeholder="dmarc_aggregate"
        @update:model-value="update('aggregate_topic', $event)"
      />
      <AppInput
        label="Forensic Topic"
        :model-value="model.forensic_topic"
        placeholder="dmarc_forensic"
        @update:model-value="update('forensic_topic', $event)"
      />
      <AppInput
        label="SMTP TLS Topic"
        :model-value="model.smtp_tls_topic"
        placeholder="smtp_tls"
        @update:model-value="update('smtp_tls_topic', $event)"
      />
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <AppInput
        label="Username"
        :model-value="model.username ?? ''"
        placeholder="Optional SASL username"
        @update:model-value="update('username', $event || undefined)"
      />
      <PasswordInput
        label="Password"
        :model-value="model.password ?? ''"
        placeholder="Optional SASL password"
        @update:model-value="update('password', $event || undefined)"
      />
    </div>
    <AppToggle
      label="Use SSL/TLS"
      :model-value="model.ssl"
      @update:model-value="update('ssl', $event)"
    />
  </FormSection>
</template>
