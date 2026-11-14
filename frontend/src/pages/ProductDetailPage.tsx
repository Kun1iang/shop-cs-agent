import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../api/products'
import { formatMoney } from '../utils/money'

export function ProductDetailPage() {
  const { slug } = useParams()
  const productQuery = useQuery({
    queryKey: ['product', slug],
    queryFn: ({ signal }) => fetchProduct(slug ?? '', signal),
    enabled: Boolean(slug),
  })

  if (productQuery.isPending) {
    return <div className="detail-state">正在加载商品详情…</div>
  }

  if (productQuery.isError || !productQuery.data) {
    return (
      <div className="detail-state">
        <strong>无法打开商品</strong>
        <p>
          {productQuery.error instanceof Error
            ? productQuery.error.message
            : '商品不存在'}
        </p>
        <Link to="/">返回商品列表</Link>
      </div>
    )
  }

  const product = productQuery.data

  return (
    <article className="product-detail">
      <Link className="back-link" to="/">
        ← 返回商品列表
      </Link>

      <div className="detail-layout">
        <div className="detail-visual">
          <img
            src={product.primary_image_url ?? '/product-placeholder.svg'}
            alt={product.name}
          />
        </div>

        <div className="detail-content">
          <span className="eyebrow">{product.category.name}</span>
          <h1>{product.name}</h1>
          <p className="detail-summary">{product.summary}</p>
          <strong className="detail-price">
            {formatMoney(product.price_from_cents)}
          </strong>

          <div className="detail-description">
            <span className="section-kicker">DETAILS</span>
            <p>{product.description}</p>
          </div>

          <div className="variant-list">
            <span>可选规格</span>
            {product.variants.map((variant) => (
              <div className="variant-row" key={variant.id}>
                <span>{variant.name}</span>
                <span>{formatMoney(variant.price_cents)}</span>
                <small>库存 {variant.stock}</small>
              </div>
            ))}
          </div>

          <button className="cart-placeholder" type="button" disabled>
            购物车将在下一阶段开放
          </button>
        </div>
      </div>
    </article>
  )
}

