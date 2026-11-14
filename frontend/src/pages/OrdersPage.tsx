import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchOrders } from '../api/orders'
import { formatMoney } from '../utils/money'

const statusLabels: Record<string, string> = {
  paid: '已支付（模拟）',
  created: '待支付',
  shipped: '已发货',
  delivered: '已签收',
  cancelled: '已取消',
}

export function OrdersPage() {
  const ordersQuery = useQuery({
    queryKey: ['orders'],
    queryFn: ({ signal }) => fetchOrders(signal),
  })

  if (ordersQuery.isPending) {
    return <div className="detail-state">正在读取订单…</div>
  }

  if (ordersQuery.isError) {
    return (
      <div className="detail-state" role="alert">
        <strong>订单加载失败</strong>
        <p>
          {ordersQuery.error instanceof Error
            ? ordersQuery.error.message
            : '请确认后端服务正在运行'}
        </p>
      </div>
    )
  }

  return (
    <section className="orders-page">
      <div className="page-heading">
        <span className="section-kicker">ORDERS</span>
        <h1>我的订单</h1>
        <p>模拟支付成功后会立即出现在这里。</p>
      </div>

      {ordersQuery.data.length === 0 ? (
        <div className="detail-state">
          <strong>还没有订单</strong>
          <p>先去购物车完成一次模拟结算。</p>
          <Link to="/">浏览商品</Link>
        </div>
      ) : (
        <div className="orders-list">
          {ordersQuery.data.map((order) => (
            <Link
              className="order-card"
              to={`/orders/${order.order_no}`}
              key={order.id}
            >
              <div>
                <span className="section-kicker">{order.order_no}</span>
                <h2>{order.items.map((item) => item.product_name).join('、')}</h2>
                <p>
                  {new Date(order.created_at).toLocaleString('zh-CN')} ·{' '}
                  {order.items.reduce((sum, item) => sum + item.quantity, 0)} 件
                </p>
              </div>
              <div className="order-card-side">
                <span>{statusLabels[order.status] ?? order.status}</span>
                <strong>{formatMoney(order.total_cents)}</strong>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}

