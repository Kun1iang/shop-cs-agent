import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchOrder } from '../api/orders'
import { formatMoney } from '../utils/money'

const statusLabels: Record<string, string> = {
  paid: '已支付（模拟）',
  created: '待支付',
  shipped: '已发货',
  delivered: '已签收',
  cancelled: '已取消',
}

export function OrderDetailPage() {
  const { orderNo } = useParams()
  const orderQuery = useQuery({
    queryKey: ['order', orderNo],
    queryFn: ({ signal }) => fetchOrder(orderNo ?? '', signal),
    enabled: Boolean(orderNo),
  })

  if (orderQuery.isPending) {
    return <div className="detail-state">正在读取订单详情…</div>
  }

  if (orderQuery.isError || !orderQuery.data) {
    return (
      <div className="detail-state" role="alert">
        <strong>无法打开订单</strong>
        <p>
          {orderQuery.error instanceof Error
            ? orderQuery.error.message
            : '订单不存在'}
        </p>
        <Link to="/orders">返回订单列表</Link>
      </div>
    )
  }

  const order = orderQuery.data

  return (
    <article className="order-detail">
      <Link className="back-link" to="/orders">
        ← 返回订单列表
      </Link>

      <div className="page-heading">
        <span className="section-kicker">{order.order_no}</span>
        <h1>{statusLabels[order.status] ?? order.status}</h1>
        <p>下单时间：{new Date(order.created_at).toLocaleString('zh-CN')}</p>
      </div>

      <div className="order-detail-layout">
        <div className="order-items">
          {order.items.map((item) => (
            <div className="order-item" key={item.id}>
              <div>
                <strong>{item.product_name}</strong>
                <span>
                  {item.variant_name} · {item.sku}
                </span>
              </div>
              <span>
                {formatMoney(item.unit_price_cents)} × {item.quantity}
              </span>
              <strong>{formatMoney(item.line_total_cents)}</strong>
            </div>
          ))}
        </div>

        <aside className="cart-summary">
          <span className="section-kicker">PAYMENT</span>
          <h2>金额明细</h2>
          <dl>
            <div>
              <dt>商品小计</dt>
              <dd>{formatMoney(order.subtotal_cents)}</dd>
            </div>
            <div>
              <dt>配送费</dt>
              <dd>{formatMoney(order.shipping_fee_cents)}</dd>
            </div>
            <div>
              <dt>支付方式</dt>
              <dd>模拟支付</dd>
            </div>
          </dl>
          <strong className="cart-total">
            {formatMoney(order.total_cents)}
          </strong>
          <p className="order-note">
            此订单仅用于学习演示，没有真实扣款或物流。
          </p>
        </aside>
      </div>
    </article>
  )
}

