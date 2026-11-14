export type CartProduct = {
  id: number
  name: string
  slug: string
  primary_image_url: string | null
}

export type CartVariant = {
  id: number
  name: string
  sku: string
  price_cents: number
  stock: number
}

export type CartItem = {
  id: number
  quantity: number
  unit_price_cents: number
  line_total_cents: number
  product: CartProduct
  variant: CartVariant
}

export type Cart = {
  id: number
  items: CartItem[]
  item_count: number
  subtotal_cents: number
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let message = `请求失败：HTTP ${response.status}`
    try {
      const error = (await response.json()) as { detail?: string }
      if (error.detail) {
        message = error.detail
      }
    } catch {
      // The fallback message is enough when the body is not JSON.
    }
    throw new Error(message)
  }

  return (await response.json()) as T
}

export function fetchCart(signal?: AbortSignal): Promise<Cart> {
  return requestJson<Cart>('/api/v1/cart', { signal })
}

export function addCartItem(
  variantId: number,
  quantity: number,
): Promise<Cart> {
  return requestJson<Cart>('/api/v1/cart/items', {
    method: 'POST',
    body: JSON.stringify({
      variant_id: variantId,
      quantity,
    }),
  })
}

export function updateCartItem(
  itemId: number,
  quantity: number,
): Promise<Cart> {
  return requestJson<Cart>(`/api/v1/cart/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify({ quantity }),
  })
}

export async function deleteCartItem(itemId: number): Promise<void> {
  const response = await fetch(`/api/v1/cart/items/${itemId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`删除失败：HTTP ${response.status}`)
  }
}

