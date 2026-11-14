import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchCart } from '../api/cart'
import { fetchHealth } from '../api/health'

export function StoreHeader() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
  })
  const cartQuery = useQuery({
    queryKey: ['cart'],
    queryFn: ({ signal }) => fetchCart(signal),
  })

  return (
    <header className="store-header">
      <Link className="brand" to="/" aria-label="返回桌面好物首页">
        <span className="brand-mark">栖</span>
        <span>
          <strong>桌面好物</strong>
          <small>为你的桌面挑点好东西</small>
        </span>
      </Link>

      <div className="header-actions">
        <span
          className={`api-badge ${
            healthQuery.isSuccess ? 'api-badge--online' : 'api-badge--offline'
          }`}
        >
          <i />
          {healthQuery.isSuccess ? '服务在线' : '服务离线'}
        </span>
        <Link className="cart-link" to="/cart">
          购物车
          <span>{cartQuery.data?.item_count ?? 0}</span>
        </Link>
        <Link className="orders-link" to="/orders">
          订单
        </Link>
      </div>
    </header>
  )
}

