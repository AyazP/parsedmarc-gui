export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

class ApiClient {
  async request<T>(endpoint: string, options: { method?: string; body?: unknown; headers?: Record<string, string> } = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    }

    if (body !== undefined) {
      config.body = JSON.stringify(body)
    }

    const response = await fetch(endpoint, config)

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ detail: response.statusText }))
      throw new ApiError(response.status, errorBody.detail || 'Request failed')
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint)
  }

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body })
  }

  put<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body })
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  async upload<T>(endpoint: string, file: File): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ detail: response.statusText }))
      throw new ApiError(response.status, errorBody.detail || 'Upload failed')
    }

    return response.json()
  }

  async uploadMultiple<T>(endpoint: string, files: Record<string, File | null>): Promise<T> {
    const formData = new FormData()
    for (const [field, file] of Object.entries(files)) {
      if (file) {
        formData.append(field, file)
      }
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ detail: response.statusText }))
      throw new ApiError(response.status, errorBody.detail || 'Upload failed')
    }

    return response.json()
  }
}

export const apiClient = new ApiClient()
