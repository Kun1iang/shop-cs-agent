import { Route, Routes } from 'react-router-dom'
import { StoreHeader } from './components/StoreHeader'
import { SupportWidget } from './components/SupportWidget'
import { CartPage } from './pages/CartPage'
import { HomePage } from './pages/HomePage'
import { OrderDetailPage } from './pages/OrderDetailPage'
import { OrdersPage } from './pages/OrdersPage'
import { ProductDetailPage } from './pages/ProductDetailPage'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <StoreHeader />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/:orderNo" element={<OrderDetailPage />} />
          <Route path="/products/:slug" element={<ProductDetailPage />} />
        </Routes>
      </main>
      <footer className="store-footer">
        <span>桌面好物 · 学习型商城项目</span>
        <span>React + FastAPI + SQLite</span>
      </footer>
      <SupportWidget />
    </div>
  )
}

export default App

