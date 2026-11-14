# 桌面好物 · ShopSystem Customer Service Agent

一个包含完整购物流程和全局客服 Agent 的学习型商城。

## 当前状态

本地功能 MVP 与生产形态部署已完成：

- [x] React + TypeScript + Vite 响应式商城
- [x] FastAPI + SQLAlchemy + Alembic 后端
- [x] 商品列表、分类筛选和商品详情
- [x] 购物车增删改查与库存校验
- [x] 模拟下单、订单快照和订单查询
- [x] 全局客服悬浮球与持久化会话
- [x] DeepSeek 真实对话
- [x] 订单、商品、购物车和售后政策工具调用
- [x] jieba + BM25 售后知识检索
- [x] SSE 流式传输
- [x] 转人工工单
- [x] PostgreSQL + Docker Compose + Caddy
- [x] PostgreSQL 备份与恢复验证
- [ ] 公网服务器与域名上线
- [ ] 真实用户认证与多用户隔离
- [ ] Playwright 浏览器 E2E 与 CI
- [ ] 原生模型 token 流式生成

当前是功能完整的学习项目，不是可直接处理真实支付和生产数据的商业电商平台。

## 功能

### 商城

- 3 个商品分类：数码配件、桌面小电器、办公文具。
- 6 个种子商品。
- 规格、SKU、价格和库存。
- 购物车和模拟结算。
- 订单商品快照。
- 模拟支付状态 `paid`。

### 客服 Agent

- 所有主要页面右下角“客服”悬浮球。
- 会话和消息持久化。
- 当前商品和当前订单上下文。
- 工具调用与审计：
  - `get_my_orders`
  - `get_order`
  - `get_product`
  - `get_cart`
  - `search_policy`
  - `handoff_to_human`
- 售后政策 BM25 检索。
- 转人工工单。
- SSE 分段回复。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React、TypeScript、Vite、React Router、TanStack Query |
| 后端 | Python 3.12、FastAPI、Pydantic v2 |
| 数据库 | SQLite（本地快速开发）、PostgreSQL 17（Compose） |
| ORM / 迁移 | SQLAlchemy 2、Alembic |
| Agent | DeepSeek OpenAI 兼容接口 + 自定义工具循环 |
| 检索 | jieba + rank-bm25 |
| 部署 | Docker Compose、Caddy |
| 测试 / 检查 | pytest、Ruff、ESLint、TypeScript |

## 项目结构

```text
.
├── backend/
│   ├── app/
│   ├── data/knowledge/
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   ├── Caddyfile
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── backup-postgres.sh
│   └── restore-postgres.sh
├── compose.yaml
└── README.md
```

技术方案、可行性分析、每日任务和学习记录由项目管理目录单独维护，不进入本代码仓库。

## 本地开发

### 后端

```powershell
cd backend
uv sync
Copy-Item .env.example .env
```

在 `backend/.env` 中配置：

```text
SHOP_DEEPSEEK_API_KEY=your-key
SHOP_DEEPSEEK_BASE_URL=https://api.deepseek.com
SHOP_DEEPSEEK_MODEL=deepseek-chat
```

初始化 SQLite 并启动：

```powershell
uv run alembic upgrade head
uv run python -m app.seed
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```powershell
cd frontend
npm ci
npm run dev
```

打开 `http://localhost:5173`。

## Docker Compose

```powershell
$env:POSTGRES_PASSWORD = "replace-with-a-strong-password"
$env:SITE_ADDRESS = ":80"
docker compose up -d --build
docker compose ps
```

打开 `http://localhost`。

使用域名和 HTTPS 时，将 `SITE_ADDRESS` 设置为域名，由 Caddy 处理证书。

生产环境必须在 `backend/.env` 中配置 DeepSeek Key。该文件不会进入镜像或 Git。

## 测试与检查

后端：

```powershell
cd backend
uv run pytest -q
uv run ruff check .
uv run alembic check
```

前端：

```powershell
cd frontend
npm run lint
npm run build
```

## 主要 API

```text
GET  /api/v1/health

GET  /api/v1/products
GET  /api/v1/products/{slug}

GET  /api/v1/cart
POST /api/v1/cart/items
PATCH /api/v1/cart/items/{item_id}
DELETE /api/v1/cart/items/{item_id}

POST /api/v1/orders/checkout
GET  /api/v1/orders
GET  /api/v1/orders/{order_no}

POST /api/v1/conversations
GET  /api/v1/conversations/{conversation_id}
POST /api/v1/conversations/{conversation_id}/messages
POST /api/v1/conversations/{conversation_id}/messages/stream
```

## 备份与恢复

首次在 Linux 服务器运行时：

```bash
chmod +x scripts/*.sh
```

备份：

```bash
./scripts/backup-postgres.sh
```

恢复：

```bash
./scripts/restore-postgres.sh backups/shop-YYYYMMDDTHHMMSSZ.sql
```

恢复脚本会要求输入 `YES` 确认。

## 已知限制

- 当前使用固定开发用户，不能作为正式身份认证。
- 支付、退款到账和物流均为模拟流程。
- SSE 当前是完整回答生成后的分段传输，不是原生模型 token 流。
- 尚未实现浏览器 E2E、CI、限流和公网监控。
- 公网服务器和域名尚未部署。
- 不建议录入真实手机号、地址、支付或其他敏感个人信息。

## Git

- 主分支：`main`
- 远程：`https://github.com/Kun1iang/shop-cs-agent`
- 当前工作区应保持干净，功能变更按小提交推进。
