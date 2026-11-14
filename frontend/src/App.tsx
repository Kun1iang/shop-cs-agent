import { Route, Routes } from 'react-router-dom'
import { StoreHeader } from './components/StoreHeader'
import { CartPage } from './pages/CartPage'
import { HomePage } from './pages/HomePage'
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
          <Route path="/products/:slug" element={<ProductDetailPage />} />
        </Routes>
      </main>
      <footer className="store-footer">
        <span>桌面好物 · 学习型商城项目</span>
        <span>React + FastAPI + SQLite</span>
      </footer>
    </div>
  )
}

export default App

