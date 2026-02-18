<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useParsingStore } from '@/stores/parsing'
import { useToast } from '@/composables/useToast'
import type { ParsedReport } from '@/types/parsing'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import ReportJsonViewer from '@/components/report/ReportJsonViewer.vue'

const route = useRoute()
const router = useRouter()
const store = useParsingStore()
const toast = useToast()

const report = ref<ParsedReport | null>(null)
const loading = ref(true)
const showRawData = ref(false)
const expandedRecords = ref(new Set<number>())

const typeVariant: Record<string, 'success' | 'warning' | 'info' | 'neutral'> = {
  aggregate: 'success',
  forensic: 'warning',
  smtp_tls: 'info',
}

onMounted(async () => {
  const id = Number(route.params.id)
  const result = await store.getReport(id)
  if (!result) {
    toast.error('Report not found.')
    router.replace('/reports')
    return
  }
  report.value = result
  loading.value = false
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const parsedData = computed<any>(() => {
  if (!report.value?.report_json) return null
  try {
    return typeof report.value.report_json === 'string'
      ? JSON.parse(report.value.report_json)
      : report.value.report_json
  } catch {
    return null
  }
})

const isAggregate = computed(() => report.value?.report_type === 'aggregate')

const policyPublished = computed(() => parsedData.value?.policy_published ?? null)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const records = computed<any[]>(() => parsedData.value?.records ?? [])

const totalMessages = computed(() =>
  records.value.reduce((sum: number, r: { count?: number }) => sum + (r.count || 0), 0)
)

const passingMessages = computed(() =>
  records.value
    .filter((r: { policy_evaluated?: { disposition?: string } }) =>
      r.policy_evaluated?.disposition === 'none'
    )
    .reduce((sum: number, r: { count?: number }) => sum + (r.count || 0), 0)
)

const passRate = computed(() =>
  totalMessages.value > 0 ? Math.round((passingMessages.value / totalMessages.value) * 100) : 0
)

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function alignmentLabel(mode: string | undefined): string {
  if (mode === 's') return 'Strict'
  if (mode === 'r') return 'Relaxed'
  return mode ?? '-'
}

function policyLabel(p: string | undefined): string {
  if (p === 'none') return 'None (monitor)'
  if (p === 'quarantine') return 'Quarantine'
  if (p === 'reject') return 'Reject'
  return p ?? '-'
}

function policyVariant(p: string | undefined): 'success' | 'warning' | 'error' | 'neutral' {
  if (p === 'none') return 'info' as 'neutral'
  if (p === 'quarantine') return 'warning'
  if (p === 'reject') return 'error'
  return 'neutral'
}

function passFailVariant(val: string | boolean | undefined): 'success' | 'error' | 'neutral' {
  if (val === 'pass' || val === true) return 'success'
  if (val === 'fail' || val === false) return 'error'
  return 'neutral'
}

function passFailText(val: string | boolean | undefined): string {
  if (val === true) return 'Pass'
  if (val === false) return 'Fail'
  if (typeof val === 'string') return val.charAt(0).toUpperCase() + val.slice(1)
  return '-'
}

function dispositionVariant(d: string | undefined): 'success' | 'warning' | 'error' | 'neutral' {
  if (d === 'none') return 'success'
  if (d === 'quarantine') return 'warning'
  if (d === 'reject') return 'error'
  return 'neutral'
}

function dispositionLabel(d: string | undefined): string {
  if (d === 'none') return 'None (delivered)'
  if (d === 'quarantine') return 'Quarantine'
  if (d === 'reject') return 'Reject'
  return d ?? '-'
}

function toggleRecord(index: number) {
  const s = new Set(expandedRecords.value)
  if (s.has(index)) s.delete(index)
  else s.add(index)
  expandedRecords.value = s
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <AppButton variant="ghost" @click="router.push('/reports')">
        &larr; Back
      </AppButton>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Report Detail</h1>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" />
    </div>

    <template v-else-if="report">
      <!-- Metadata -->
      <AppCard>
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Metadata</h2>
        </template>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</p>
            <div class="mt-1"><AppBadge :text="report.report_type" :variant="typeVariant[report.report_type] ?? 'neutral'" /></div>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Organization</p>
            <p class="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{{ report.org_name ?? '-' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Domain</p>
            <p class="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{{ report.domain ?? '-' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Report ID</p>
            <p class="mt-1 text-sm font-mono text-gray-600 dark:text-gray-400 break-all">{{ report.report_id ?? '-' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date Range</p>
            <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">
              {{ formatDate(report.date_begin) }} — {{ formatDate(report.date_end) }}
            </p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Imported</p>
            <p class="mt-1 text-sm text-gray-900 dark:text-gray-100">{{ formatDate(report.created_at) }}</p>
          </div>
        </div>
      </AppCard>

      <!-- DMARC Results Summary (aggregate reports) -->
      <AppCard v-if="isAggregate && parsedData">
        <template #header>
          <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">DMARC Results</h2>
        </template>
        <div class="space-y-6">
          <!-- Compliance overview -->
          <div>
            <div class="flex items-baseline justify-between mb-2">
              <div>
                <span class="text-3xl font-bold" :class="passRate >= 100 ? 'text-green-600 dark:text-green-400' : passRate >= 80 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'">
                  {{ passRate }}%
                </span>
                <span class="text-sm text-gray-500 dark:text-gray-400 ml-2">DMARC compliance</span>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-400">
                {{ passingMessages }} of {{ totalMessages }} message{{ totalMessages !== 1 ? 's' : '' }} passed
              </p>
            </div>
            <div class="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="passRate >= 100 ? 'bg-green-500' : passRate >= 80 ? 'bg-yellow-500' : 'bg-red-500'"
                :style="{ width: passRate + '%' }"
              />
            </div>
          </div>

          <!-- Policy Published -->
          <div v-if="policyPublished">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Published Policy</h3>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Domain Policy</p>
                <div class="mt-1"><AppBadge :text="policyLabel(policyPublished.p)" :variant="policyVariant(policyPublished.p)" /></div>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Subdomain Policy</p>
                <div class="mt-1"><AppBadge :text="policyLabel(policyPublished.sp)" :variant="policyVariant(policyPublished.sp)" /></div>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">DKIM Alignment</p>
                <p class="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{{ alignmentLabel(policyPublished.adkim) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">SPF Alignment</p>
                <p class="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{{ alignmentLabel(policyPublished.aspf) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Percentage</p>
                <p class="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{{ policyPublished.pct ?? '-' }}%</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Failure Reporting</p>
                <p class="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{{ policyPublished.fo ?? '-' }}</p>
              </div>
            </div>
          </div>
        </div>
      </AppCard>

      <!-- Source Analysis (aggregate reports) -->
      <AppCard v-if="isAggregate && records.length > 0">
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">
              Source Analysis
              <span class="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">({{ records.length }} source{{ records.length !== 1 ? 's' : '' }})</span>
            </h2>
          </div>
        </template>
        <div class="space-y-3">
          <div
            v-for="(record, idx) in records"
            :key="idx"
            class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          >
            <!-- Record summary row -->
            <div
              class="flex flex-wrap items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              @click="toggleRecord(idx)"
            >
              <!-- Expand icon -->
              <span class="text-gray-400 dark:text-gray-500 text-xs w-4 flex-shrink-0">
                {{ expandedRecords.has(idx) ? '&#9660;' : '&#9654;' }}
              </span>

              <!-- Source IP -->
              <div class="min-w-[140px]">
                <p class="text-sm font-mono font-semibold text-gray-900 dark:text-gray-100">
                  {{ record.source?.ip_address ?? '-' }}
                </p>
                <p v-if="record.source?.reverse_dns" class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                  {{ record.source.reverse_dns }}
                </p>
              </div>

              <!-- Country -->
              <span v-if="record.source?.country" class="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                {{ record.source.country }}
              </span>

              <!-- Message count -->
              <span class="text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">
                {{ record.count ?? 0 }} msg{{ (record.count ?? 0) !== 1 ? 's' : '' }}
              </span>

              <!-- Spacer -->
              <div class="flex-1" />

              <!-- Result badges -->
              <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center gap-1">
                  <span class="text-xs text-gray-500 dark:text-gray-400">SPF</span>
                  <AppBadge :text="passFailText(record.policy_evaluated?.spf)" :variant="passFailVariant(record.policy_evaluated?.spf)" />
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-xs text-gray-500 dark:text-gray-400">DKIM</span>
                  <AppBadge :text="passFailText(record.policy_evaluated?.dkim)" :variant="passFailVariant(record.policy_evaluated?.dkim)" />
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-xs text-gray-500 dark:text-gray-400">DMARC</span>
                  <AppBadge
                    :text="record.alignment?.dmarc ? 'Aligned' : 'Not Aligned'"
                    :variant="record.alignment?.dmarc ? 'success' : 'error'"
                  />
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-xs text-gray-500 dark:text-gray-400">Action</span>
                  <AppBadge
                    :text="dispositionLabel(record.policy_evaluated?.disposition)"
                    :variant="dispositionVariant(record.policy_evaluated?.disposition)"
                  />
                </div>
              </div>
            </div>

            <!-- Expanded details -->
            <div
              v-if="expandedRecords.has(idx)"
              class="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 px-4 py-4 space-y-4"
            >
              <!-- Identifiers -->
              <div v-if="record.identifiers">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Identifiers</h4>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Header From</p>
                    <p class="mt-1 text-sm font-mono text-gray-900 dark:text-gray-100">{{ record.identifiers.header_from ?? '-' }}</p>
                  </div>
                  <div>
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Envelope From</p>
                    <p class="mt-1 text-sm font-mono text-gray-900 dark:text-gray-100">{{ record.identifiers.envelope_from ?? '-' }}</p>
                  </div>
                  <div>
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Envelope To</p>
                    <p class="mt-1 text-sm font-mono text-gray-900 dark:text-gray-100">{{ record.identifiers.envelope_to ?? '-' }}</p>
                  </div>
                </div>
              </div>

              <!-- Alignment details -->
              <div v-if="record.alignment">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Alignment</h4>
                <div class="flex items-center gap-4">
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs text-gray-600 dark:text-gray-400">SPF:</span>
                    <AppBadge :text="record.alignment.spf ? 'Aligned' : 'Not Aligned'" :variant="record.alignment.spf ? 'success' : 'error'" />
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs text-gray-600 dark:text-gray-400">DKIM:</span>
                    <AppBadge :text="record.alignment.dkim ? 'Aligned' : 'Not Aligned'" :variant="record.alignment.dkim ? 'success' : 'error'" />
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs text-gray-600 dark:text-gray-400">DMARC:</span>
                    <AppBadge :text="record.alignment.dmarc ? 'Aligned' : 'Not Aligned'" :variant="record.alignment.dmarc ? 'success' : 'error'" />
                  </div>
                </div>
              </div>

              <!-- Auth Results - DKIM -->
              <div v-if="record.auth_results?.dkim?.length">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">DKIM Authentication</h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="text-left text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                        <th class="pb-1.5 pr-4 font-medium">Domain</th>
                        <th class="pb-1.5 pr-4 font-medium">Selector</th>
                        <th class="pb-1.5 font-medium">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(dkim, di) in record.auth_results.dkim" :key="di">
                        <td class="py-1 pr-4 font-mono text-gray-900 dark:text-gray-100">{{ dkim.domain ?? '-' }}</td>
                        <td class="py-1 pr-4 font-mono text-gray-600 dark:text-gray-400">{{ dkim.selector ?? '-' }}</td>
                        <td class="py-1">
                          <AppBadge :text="passFailText(dkim.result)" :variant="passFailVariant(dkim.result)" />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Auth Results - SPF -->
              <div v-if="record.auth_results?.spf?.length">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">SPF Authentication</h4>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="text-left text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                        <th class="pb-1.5 pr-4 font-medium">Domain</th>
                        <th class="pb-1.5 pr-4 font-medium">Scope</th>
                        <th class="pb-1.5 font-medium">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(spf, si) in record.auth_results.spf" :key="si">
                        <td class="py-1 pr-4 font-mono text-gray-900 dark:text-gray-100">{{ spf.domain ?? '-' }}</td>
                        <td class="py-1 pr-4 font-mono text-gray-600 dark:text-gray-400">{{ spf.scope ?? '-' }}</td>
                        <td class="py-1">
                          <AppBadge :text="passFailText(spf.result)" :variant="passFailVariant(spf.result)" />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Policy override reasons -->
              <div v-if="record.policy_evaluated?.policy_override_reasons?.length">
                <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Policy Override Reasons</h4>
                <ul class="list-disc list-inside text-sm text-gray-700 dark:text-gray-300">
                  <li v-for="(reason, ri) in record.policy_evaluated.policy_override_reasons" :key="ri">
                    <span class="font-medium">{{ reason.type ?? reason }}</span>
                    <span v-if="reason.comment" class="text-gray-500 dark:text-gray-400"> — {{ reason.comment }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </AppCard>

      <!-- Raw Report Data (collapsible) -->
      <AppCard>
        <template #header>
          <div
            class="flex items-center justify-between cursor-pointer select-none"
            @click="showRawData = !showRawData"
          >
            <h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">Raw Report Data</h2>
            <span class="text-gray-400 dark:text-gray-500 text-sm">
              {{ showRawData ? '&#9660;' : '&#9654;' }}
            </span>
          </div>
        </template>
        <div v-if="showRawData">
          <ReportJsonViewer :data="parsedData ?? report.report_json" />
        </div>
        <p v-else class="text-sm text-gray-500 dark:text-gray-400">
          Click to expand raw report JSON data.
        </p>
      </AppCard>
    </template>
  </div>
</template>
