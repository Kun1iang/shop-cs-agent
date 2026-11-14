export type HealthResponse = {
  status: string
  service: string
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch('/api/v1/health', {
    headers: {
      Accept: 'application/json',
    },
    signal,
  })

  if (!response.ok) {
    throw new Error(`后端返回 HTTP ${response.status}`)
  }

  const data: unknown = await response.json()

  if (
    typeof data !== 'object' ||
    data === null ||
    !('status' in data) ||
    !('service' in data) ||
    typeof data.status !== 'string' ||
    typeof data.service !== 'string'
  ) {
    throw new Error('后端返回的数据格式不正确')
  }

  return {
    status: data.status,
    service: data.service,
  }
}

