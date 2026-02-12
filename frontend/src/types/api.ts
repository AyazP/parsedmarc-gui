export interface ApiError {
  detail: string
}

export interface SetupStepResponse {
  success: boolean
  message: string
  data?: Record<string, unknown>
  errors?: Record<string, string>
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
}
