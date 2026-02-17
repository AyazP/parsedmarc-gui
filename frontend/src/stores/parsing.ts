import { ref } from 'vue'
import { defineStore } from 'pinia'
import { parsingApi } from '@/api/parsing'
import type { ParseJob, ParsedReport, ReportFilters } from '@/types/parsing'

export const useParsingStore = defineStore('parsing', () => {
  const jobs = ref<ParseJob[]>([])
  const jobsLoading = ref(false)

  const reports = ref<ParsedReport[]>([])
  const reportsTotal = ref(0)
  const reportsLoading = ref(false)

  const filters = ref<ReportFilters>({})

  async function fetchJobs(params: { skip?: number; limit?: number; status?: string } = {}) {
    jobsLoading.value = true
    try {
      jobs.value = await parsingApi.listJobs(params)
    } catch {
      // handled by view
    } finally {
      jobsLoading.value = false
    }
  }

  async function fetchReports(params: {
    skip?: number
    limit?: number
    report_type?: string
    domain?: string
    org_name?: string
  } = {}) {
    reportsLoading.value = true
    try {
      const result = await parsingApi.listReports(params)
      reports.value = result.items
      reportsTotal.value = result.total
    } catch {
      // handled by view
    } finally {
      reportsLoading.value = false
    }
  }

  async function getReport(id: number): Promise<ParsedReport | null> {
    try {
      return await parsingApi.getReport(id)
    } catch {
      return null
    }
  }

  async function uploadFile(file: File): Promise<ParseJob> {
    return await parsingApi.uploadFile(file)
  }

  return {
    jobs,
    jobsLoading,
    reports,
    reportsTotal,
    reportsLoading,
    filters,
    fetchJobs,
    fetchReports,
    getReport,
    uploadFile,
  }
})
