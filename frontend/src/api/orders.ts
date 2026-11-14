export type OrderItem = {
  id: number
  product_id: number
  variant_id: number
  product_name: string
  variant_name: string
  sku: string
  unit_price_cents: number
  quantity: number
  line_total_cents: number
}

export type Order = {
  id: number
  order_no: string
  status: string
  subtotal_cents: number
  shipping_fee_cents: number
  total_cents: number
  created_at: string
  items: OrderItem[]
}

async function parseError(response: Response): Promise<Error> {
  let message = `请求失败：HTTP ${response.status}`
  try {
    const error = (await response.json()) as { detail?: string }
    if (error.detail) {
      message = error.detail
    }
  } catch {
    // Keep the HTTP fallback when the server did not return JSON.
  }
  return new Error(message)
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  })
  if (!response.ok) {
    throw await parseError(response)
  }
  return (await response.json()) as T
}

export function checkoutOrder(idempotencyKey: string): Promise<Order> {
  return requestJson<Order>('/api/v1/orders/checkout', {
    method: 'POST',
    headers: {
      'Idempotency-Key': idempotencyKey,
    },
  })
}

export function fetchOrders(signal?: AbortSignal): Promise<Order[]> {
  return requestJson<Order[]>('/api/v1/orders', { signal })
}

export function fetchOrder(
  orderNo: string,
  signal?: AbortSignal,
): Promise<Order> {
  return requestJson<Order>(`/api/v1/orders/${encodeURIComponent(orderNo)}`, {
    signal,
  })
}

