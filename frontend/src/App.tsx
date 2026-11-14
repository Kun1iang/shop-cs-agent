import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from './api/health'
import './App.css'

function App() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
  })

  return (
    <main className="app-shell">
      <header className="hero">
        <span className="eyebrow">S1 · 前后端连通</span>
        <h1>无名小店</h1>
        <p>
          响应式商城与全局客服 Agent 正在搭建。今天先确认浏览器能够通过真实
          HTTP 请求访问后端。
        </p>
      </header>

      <section className="status-grid" aria-live="polite">
        <article className="status-card">
          <span className="card-label">API 状态</span>

          {healthQuery.isPending ? (
            <div className="status-value status-value--pending">
              <span className="status-dot" />
              正在连接后端
            </div>
          ) : null}

          {healthQuery.isError ? (
            <>
              <div className="status-value status-value--error">
                <span className="status-dot" />
                后端未连接
              </div>
              <p className="status-detail">
                {healthQuery.error instanceof Error
                  ? healthQuery.error.message
                  : '无法访问健康接口'}
              </p>
              <button
                type="button"
                className="retry-button"
                onClick={() => {
                  void healthQuery.refetch()
                }}
              >
                重新连接
              </button>
            </>
          ) : null}

          {healthQuery.isSuccess ? (
            <>
              <div className="status-value status-value--success">
                <span className="status-dot" />
                后端已连接
              </div>
              <p className="status-detail">
                服务：{healthQuery.data.service}
              </p>
            </>
          ) : null}
        </article>

        <article className="status-card">
          <span className="card-label">请求路径</span>
          <code>GET /api/v1/health</code>
          <p className="status-detail">
            浏览器请求 Vite，再由开发代理转发到 FastAPI。
          </p>
        </article>

        <article className="status-card">
          <span className="card-label">下一阶段</span>
          <strong>商品列表与详情</strong>
          <p className="status-detail">
            先完成健康检查，再让 6 个种子商品走通数据库、API 和页面。
          </p>
        </article>
      </section>

      <footer className="footer">
        <span>前端：React + TypeScript</span>
        <span>后端：FastAPI + Python 3.12</span>
        {healthQuery.isFetching && !healthQuery.isPending ? (
          <span>正在刷新状态…</span>
        ) : null}
      </footer>
    </main>
  )
}

export default App

