<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMailboxStore } from '@/stores/mailboxes'
import { useToast } from '@/composables/useToast'
import type {
  MailboxType,
  IMAPSettings,
  MSGraphSettings,
  GmailSettings,
  MaildirSettings,
  MailboxConfigCreate,
  MailboxConfigUpdate,
} from '@/types/mailbox'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppToggle from '@/components/ui/AppToggle.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import ImapSettingsForm from '@/components/mailbox/ImapSettingsForm.vue'
import MsGraphSettingsForm from '@/components/mailbox/MsGraphSettingsForm.vue'
import GmailSettingsForm from '@/components/mailbox/GmailSettingsForm.vue'
import MaildirSettingsForm from '@/components/mailbox/MaildirSettingsForm.vue'

const route = useRoute()
const router = useRouter()
const store = useMailboxStore()
const toast = useToast()

const editId = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})
const isEdit = computed(() => editId.value !== null)
const pageLoading = ref(false)
const saving = ref(false)
const formError = ref<string | null>(null)

// Form state
const name = ref('')
const type = ref<MailboxType>('imap')
const enabled = ref(true)
const deleteAfterProcessing = ref(false)
const watchInterval = ref(300)

const imapSettings = ref<IMAPSettings>({
  host: '',
  port: 993,
  username: '',
  password: '',
  ssl: true,
  skip_certificate_verification: false,
  folder: 'INBOX',
  batch_size: 10,
})

const msgraphSettings = ref<MSGraphSettings>({
  auth_method: 'ClientSecret',
  tenant_id: '',
  client_id: '',
  client_secret: '',
  username: '',
  password: '',
  mailbox: '',
  graph_url: 'https://graph.microsoft.com/v1.0',
  batch_size: 10,
})

const gmailSettings = ref<GmailSettings>({
  credentials_file: '',
  scopes: ['https://www.googleapis.com/auth/gmail.modify'],
  include_spam_trash: false,
  batch_size: 10,
})

const maildirSettings = ref<MaildirSettings>({
  path: '',
})

const typeOptions = [
  { value: 'imap', label: 'IMAP' },
  { value: 'msgraph', label: 'Microsoft Graph' },
  { value: 'gmail', label: 'Gmail' },
  { value: 'maildir', label: 'Maildir' },
]

onMounted(async () => {
  if (!isEdit.value) return
  pageLoading.value = true
  try {
    const config = await store.getConfig(editId.value!)
    if (!config) {
      toast.error('Mailbox config not found.')
      router.replace('/mailboxes')
      return
    }
    name.value = config.name
    type.value = config.type
    enabled.value = config.enabled
    deleteAfterProcessing.value = config.delete_after_processing
    watchInterval.value = config.watch_interval

    if (config.type === 'imap' && config.imap_settings) {
      imapSettings.value = { ...imapSettings.value, ...config.imap_settings } as IMAPSettings
    } else if (config.type === 'msgraph' && config.msgraph_settings) {
      msgraphSettings.value = { ...msgraphSettings.value, ...config.msgraph_settings } as MSGraphSettings
    } else if (config.type === 'gmail' && config.gmail_settings) {
      gmailSettings.value = { ...gmailSettings.value, ...config.gmail_settings } as GmailSettings
    } else if (config.type === 'maildir' && config.maildir_settings) {
      maildirSettings.value = { ...maildirSettings.value, ...config.maildir_settings } as MaildirSettings
    }
  } catch {
    toast.error('Failed to load mailbox config.')
    router.replace('/mailboxes')
  } finally {
    pageLoading.value = false
  }
})

function getTypeSettings(): Record<string, unknown> {
  const settingsMap: Record<MailboxType, Record<string, unknown>> = {
    imap: { imap_settings: imapSettings.value },
    msgraph: { msgraph_settings: msgraphSettings.value },
    gmail: { gmail_settings: gmailSettings.value },
    maildir: { maildir_settings: maildirSettings.value },
  }
  return settingsMap[type.value]
}

async function handleSubmit() {
  formError.value = null

  if (!name.value.trim()) {
    formError.value = 'Name is required.'
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      const data: MailboxConfigUpdate = {
        name: name.value,
        enabled: enabled.value,
        delete_after_processing: deleteAfterProcessing.value,
        watch_interval: watchInterval.value,
        ...getTypeSettings(),
      }
      await store.updateConfig(editId.value!, data)
      toast.success('Mailbox config updated.')
    } else {
      const data: MailboxConfigCreate = {
        name: name.value,
        type: type.value,
        enabled: enabled.value,
        delete_after_processing: deleteAfterProcessing.value,
        watch_interval: watchInterval.value,
        ...getTypeSettings(),
      }
      await store.createConfig(data)
      toast.success('Mailbox config created.')
    }
    router.push('/mailboxes')
  } catch (e: unknown) {
    const err = e as { detail?: string; message?: string }
    formError.value = err.detail || err.message || 'Failed to save mailbox config.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <AppButton variant="ghost" @click="router.push('/mailboxes')">
        &larr; Back
      </AppButton>
      <h1 class="text-2xl font-bold text-gray-900">
        {{ isEdit ? 'Edit Mailbox' : 'New Mailbox' }}
      </h1>
    </div>

    <div v-if="pageLoading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <AppAlert v-if="formError" variant="error" :message="formError" dismissible @dismiss="formError = null" />

      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900">General</h2>
        </template>
        <div class="space-y-4">
          <AppInput
            label="Name"
            v-model="name"
            placeholder="My DMARC Mailbox"
          />
          <AppSelect
            label="Type"
            :model-value="type"
            :options="typeOptions"
            :disabled="isEdit"
            @update:model-value="type = $event as MailboxType"
          />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <AppInput
              label="Watch Interval (seconds)"
              type="number"
              :model-value="String(watchInterval)"
              help-text="How often to check for new reports."
              @update:model-value="watchInterval = Number($event)"
            />
          </div>
          <div class="flex flex-col gap-3">
            <AppToggle v-model="enabled" label="Enabled" />
            <AppToggle v-model="deleteAfterProcessing" label="Delete messages after processing" />
          </div>
        </div>
      </AppCard>

      <AppCard>
        <ImapSettingsForm v-if="type === 'imap'" v-model="imapSettings" />
        <MsGraphSettingsForm v-else-if="type === 'msgraph'" v-model="msgraphSettings" />
        <GmailSettingsForm v-else-if="type === 'gmail'" v-model="gmailSettings" />
        <MaildirSettingsForm v-else-if="type === 'maildir'" v-model="maildirSettings" />
      </AppCard>

      <div class="flex justify-end gap-3">
        <AppButton variant="secondary" @click="router.push('/mailboxes')">Cancel</AppButton>
        <AppButton type="submit" :loading="saving">
          {{ isEdit ? 'Save Changes' : 'Create Mailbox' }}
        </AppButton>
      </div>
    </form>
  </div>
</template>
