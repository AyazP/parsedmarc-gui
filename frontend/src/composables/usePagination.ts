import { ref, computed } from 'vue'

export function usePagination(defaultPageSize = 50) {
  const currentPage = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)

  const skip = computed(() => (currentPage.value - 1) * pageSize.value)
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const hasNext = computed(() => currentPage.value < totalPages.value)
  const hasPrev = computed(() => currentPage.value > 1)

  function goToPage(page: number) {
    currentPage.value = Math.max(1, Math.min(page, totalPages.value))
  }
  function nextPage() {
    if (hasNext.value) currentPage.value++
  }
  function prevPage() {
    if (hasPrev.value) currentPage.value--
  }
  function setTotal(n: number) {
    total.value = n
  }

  return { currentPage, pageSize, total, skip, totalPages, hasNext, hasPrev, goToPage, nextPage, prevPage, setTotal }
}
