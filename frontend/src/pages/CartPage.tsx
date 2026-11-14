import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  deleteCartItem,
  fetchCart,
  updateCartItem,
} from '../api/cart'
import { formatMoney } from '../utils/money'

export function CartPage() {
  const queryClient = useQueryClient()
  const cartQuery = useQuery({
    queryKey: ['cart'],
    queryFn: ({ signal }) => fetchCart(signal),
  })

  const updateMutation = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: number; quantity: number }) =>
      updateCartItem(itemId, quantity),
    onSuccess: (cart) => {
      queryClient.setQueryData(['cart'], cart)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCartItem,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })

  const cart = cartQuery.data

  if (cartQuery.isPending) {
    return <div className="detail-state">正在读取购物车…</div>
  }

  if (cartQuery.isError) {
    return (
      <div className="detail-state" role="alert">
        <strong>购物车加载失败</strong>
        <p>
          {cartQuery.error instanceof Error
            ? cartQuery.error.message
            : '请确认后端服务正在运行'}
        </p>
        <button
          type="button"
          onClick={() => {
            void cartQuery.refetch()
          }}
        >
          重新加载
        </button>
      </div>
    )
  }

  if (!cart) {
    return <div className="detail-state">购物车数据暂时不可用。</div>
  }

  return (
    <section className="cart-page">
      <div className="page-heading">
        <span className="section-kicker">CART</span>
        <h1>购物车</h1>
        <p>{cart.item_count} 件商品正在等待结算。</p>
      </div>

      {cart.items.length === 0 ? (
        <div className="detail-state">
          <strong>购物车还是空的</strong>
          <p>去商品目录挑一件适合你的桌面好物。</p>
          <Link to="/">浏览商品</Link>
        </div>
      ) : (
        <div className="cart-layout">
          <div className="cart-items">
            {cart.items.map((item) => (
              <article className="cart-item" key={item.id}>
                <Link to={`/products/${item.product.slug}`}>
                  <img
                    src={
                      item.product.primary_image_url ??
                      '/product-placeholder.svg'
                    }
                    alt={item.product.name}
                  />
                </Link>

                <div className="cart-item-main">
                  <div>
                    <span>{item.product.name}</span>
                    <small>
                      规格：{item.variant.name} · {item.variant.sku}
                    </small>
                  </div>
                  <strong>{formatMoney(item.unit_price_cents)}</strong>
                </div>

                <div className="quantity-control" aria-label="修改商品数量">
                  <button
                    type="button"
                    disabled={item.quantity <= 1 || updateMutation.isPending}
                    onClick={() =>
                      updateMutation.mutate({
                        itemId: item.id,
                        quantity: item.quantity - 1,
                      })
                    }
                  >
                    −
                  </button>
                  <span>{item.quantity}</span>
                  <button
                    type="button"
                    disabled={
                      item.quantity >= item.variant.stock ||
                      updateMutation.isPending
                    }
                    onClick={() =>
                      updateMutation.mutate({
                        itemId: item.id,
                        quantity: item.quantity + 1,
                      })
                    }
                  >
                    +
                  </button>
                </div>

                <strong className="line-total">
                  {formatMoney(item.line_total_cents)}
                </strong>

                <button
                  className="remove-item"
                  type="button"
                  disabled={deleteMutation.isPending}
                  onClick={() => deleteMutation.mutate(item.id)}
                >
                  删除
                </button>
              </article>
            ))}
          </div>

          <aside className="cart-summary">
            <span className="section-kicker">SUMMARY</span>
            <h2>订单小计</h2>
            <dl>
              <div>
                <dt>商品数量</dt>
                <dd>{cart.item_count}</dd>
              </div>
              <div>
                <dt>商品小计</dt>
                <dd>{formatMoney(cart.subtotal_cents)}</dd>
              </div>
              <div>
                <dt>配送费</dt>
                <dd>模拟免运费</dd>
              </div>
            </dl>
            <strong className="cart-total">
              {formatMoney(cart.subtotal_cents)}
            </strong>
            <button className="checkout-placeholder" type="button" disabled>
              模拟结算将在下一阶段开放
            </button>
          </aside>
        </div>
      )}

      {updateMutation.isError || deleteMutation.isError ? (
        <p className="cart-error" role="alert">
          {(updateMutation.error ?? deleteMutation.error) instanceof Error
            ? (updateMutation.error ?? deleteMutation.error)?.message
            : '购物车更新失败'}
        </p>
      ) : null}
    </section>
  )
}
