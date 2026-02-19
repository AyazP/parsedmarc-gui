export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

/**
 * Read the CSRF token from the csrf_token cookie (set by the backend on login).
 * Returns empty string if the cookie is not found.
 */
function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

/**
 * Handle 401 responses by redirecting to the login page.
 * Skips redirect if already on /login or /setup.
 */
function handleUnauthorized(): void {
  const path = window.location.pathname
  if (path !== '/login' && !path.startsWith('/setup')) {
    window.location.href = '/login'
  }
}

class ApiClient {
  async request<T>(endpoint: string, options: { method?: string; body?: unknown; headers?: Record<string, string> } = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options

    // Add CSRF token header for state-changing methods
    if (method !== 'GET') {
      const csrf = getCsrfToken()
      if (csrf) {
        headers['X-CSRF-Token'] = csrf
      }
    }

    const config: RequestInit = {
      method,
      credentials: 'same-origin',
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
      if (response.status === 401) {
        handleUnauthorized()
        throw new ApiError(401, 'Session expired')
      }
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

    const csrfHeaders: Record<string, string> = {}
    const csrf = getCsrfToken()
    if (csrf) {
      csrfHeaders['X-CSRF-Token'] = csrf
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      credentials: 'same-origin',
      headers: csrfHeaders,
      body: formData,
    })

    if (!response.ok) {
      if (response.status === 401) {
        handleUnauthorized()
        throw new ApiError(401, 'Session expired')
      }
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

    const csrfHeaders: Record<string, string> = {}
    const csrf = getCsrfToken()
    if (csrf) {
      csrfHeaders['X-CSRF-Token'] = csrf
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      credentials: 'same-origin',
      headers: csrfHeaders,
      body: formData,
    })

    if (!response.ok) {
      if (response.status === 401) {
        handleUnauthorized()
        throw new ApiError(401, 'Session expired')
      }
      const errorBody = await response.json().catch(() => ({ detail: response.statusText }))
      throw new ApiError(response.status, errorBody.detail || 'Upload failed')
    }

    return response.json()
  }
}

export const apiClient = new ApiClient()
