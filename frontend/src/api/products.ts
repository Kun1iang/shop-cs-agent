export type Category = {
  id: number
  name: string
  slug: string
}

export type ProductVariant = {
  id: number
  name: string
  sku: string
  price_cents: number
  stock: number
  is_active: boolean
}

export type ProductImage = {
  url: string
  alt: string
}

export type Product = {
  id: number
  name: string
  slug: string
  summary: string
  primary_image_url: string | null
  price_from_cents: number
  stock_total: number
  category: Category
  variants: ProductVariant[]
}

export type ProductDetail = Product & {
  description: string
  images: ProductImage[]
}

async function requestJson<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, {
    headers: {
      Accept: 'application/json',
    },
    signal,
  })

  if (!response.ok) {
    throw new Error(`请求失败：HTTP ${response.status}`)
  }

  return (await response.json()) as T
}

export function fetchProducts(signal?: AbortSignal): Promise<Product[]> {
  return requestJson<Product[]>('/api/v1/products', signal)
}

export function fetchProduct(
  slug: string,
  signal?: AbortSignal,
): Promise<ProductDetail> {
  return requestJson<ProductDetail>(
    `/api/v1/products/${encodeURIComponent(slug)}`,
    signal,
  )
}

