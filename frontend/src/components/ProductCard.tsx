import { Link } from 'react-router-dom'
import type { Product } from '../api/products'
import { formatMoney } from '../utils/money'

type ProductCardProps = {
  product: Product
}

export function ProductCard({ product }: ProductCardProps) {
  return (
    <article className="product-card">
      <Link className="product-image-link" to={`/products/${product.slug}`}>
        <img
          src={product.primary_image_url ?? '/product-placeholder.svg'}
          alt={product.name}
        />
        <span className="category-tag">{product.category.name}</span>
      </Link>

      <div className="product-card-body">
        <h2>
          <Link to={`/products/${product.slug}`}>{product.name}</Link>
        </h2>
        <p>{product.summary}</p>
        <div className="product-card-footer">
          <div>
            <span className="price">{formatMoney(product.price_from_cents)}</span>
            <small>库存 {product.stock_total}</small>
          </div>
          <Link
            className="view-product"
            to={`/products/${product.slug}`}
            aria-label={`查看${product.name}详情`}
          >
            查看
          </Link>
        </div>
      </div>
    </article>
  )
}

