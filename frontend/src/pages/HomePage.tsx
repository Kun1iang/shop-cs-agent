import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts } from '../api/products'
import { ProductCard } from '../components/ProductCard'

export function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedCategory = searchParams.get('category')

  const productsQuery = useQuery({
    queryKey: ['products'],
    queryFn: ({ signal }) => fetchProducts(signal),
  })

  const categories = useMemo(() => {
    const unique = new Map(
      (productsQuery.data ?? []).map((product) => [
        product.category.slug,
        product.category,
      ]),
    )
    return [...unique.values()]
  }, [productsQuery.data])

  const visibleProducts = useMemo(
    () =>
      (productsQuery.data ?? []).filter(
        (product) =>
          selectedCategory === null ||
          product.category.slug === selectedCategory,
      ),
    [productsQuery.data, selectedCategory],
  )

  function selectCategory(slug: string | null) {
    if (slug === null) {
      setSearchParams({})
      return
    }
    setSearchParams({ category: slug })
  }

  return (
    <>
      <section className="catalog-hero">
        <div>
          <span className="eyebrow">小巧、实用、有一点讲究</span>
          <h1>让桌面更好用的日常物件</h1>
          <p>
            数码配件、桌面小电器与办公文具。首版使用仿真商品和订单数据，
            用来验证完整商城与客服 Agent 链路。
          </p>
        </div>
        <div className="hero-number" aria-hidden="true">
          06
          <span>件精选好物</span>
        </div>
      </section>

      <section className="catalog-section" aria-labelledby="catalog-title">
        <div className="catalog-toolbar">
          <div>
            <span className="section-kicker">CATALOG</span>
            <h2 id="catalog-title">全部商品</h2>
          </div>

          <div className="category-filters" aria-label="按分类筛选">
            <button
              type="button"
              className={selectedCategory === null ? 'is-active' : ''}
              onClick={() => selectCategory(null)}
            >
              全部
            </button>
            {categories.map((category) => (
              <button
                type="button"
                key={category.slug}
                className={
                  selectedCategory === category.slug ? 'is-active' : ''
                }
                onClick={() => selectCategory(category.slug)}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {productsQuery.isPending ? (
          <div className="product-grid" aria-label="正在加载商品">
            {Array.from({ length: 6 }, (_, index) => (
              <div className="product-card product-card--skeleton" key={index} />
            ))}
          </div>
        ) : null}

        {productsQuery.isError ? (
          <div className="catalog-message" role="alert">
            <strong>商品加载失败</strong>
            <p>
              {productsQuery.error instanceof Error
                ? productsQuery.error.message
                : '请确认后端服务正在运行'}
            </p>
            <button
              type="button"
              onClick={() => {
                void productsQuery.refetch()
              }}
            >
              重新加载
            </button>
          </div>
        ) : null}

        {productsQuery.isSuccess && visibleProducts.length === 0 ? (
          <div className="catalog-message">
            <strong>这个分类暂时没有商品</strong>
            <p>请选择其他分类。</p>
          </div>
        ) : null}

        {visibleProducts.length > 0 ? (
          <div className="product-grid">
            {visibleProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : null}
      </section>
    </>
  )
}

