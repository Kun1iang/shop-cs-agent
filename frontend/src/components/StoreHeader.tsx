import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchHealth } from '../api/health'

export function StoreHeader() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
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

      <span
        className={`api-badge ${
          healthQuery.isSuccess ? 'api-badge--online' : 'api-badge--offline'
        }`}
      >
        <i />
        {healthQuery.isSuccess ? '服务在线' : '服务离线'}
      </span>
    </header>
  )
}

