# ShopSystem-CustomerService-Agent

响应式 Web/PWA 商城与全局客服 Agent。

## 当前状态

代码仓库刚刚建立，正在完成 S1 工程启动：

- [ ] FastAPI 后端骨架
- [ ] React + TypeScript 前端骨架
- [ ] 前后端健康检查连通
- [ ] 商品列表与详情

## 计划结构

```text
.
├── backend/
└── frontend/
```

## 技术栈

- 前端：React + TypeScript + Vite
- 后端：Python 3.12 + FastAPI
- 本地测试：SQLite
- 公网测试：PostgreSQL
- Agent：LangGraph 自定义节点
- 测试：pytest、Vitest、Playwright

## Docker Compose

本地生产形态运行：

```powershell
$env:POSTGRES_PASSWORD = "replace-with-a-strong-password"
$env:SITE_ADDRESS = ":80"
docker compose up --build
```

打开 `http://localhost`。使用域名和 HTTPS 时，把 `SITE_ADDRESS` 设置为域名。

生产环境必须在 `backend/.env` 中配置 `SHOP_DEEPSEEK_API_KEY`。该文件不会进入镜像或 Git。

首次在 Linux 服务器运行时，为备份脚本添加执行权限：

```bash
chmod +x scripts/*.sh
```

数据库备份：

```bash
./scripts/backup-postgres.sh
```

恢复前必须先确认目标数据库，并输入 `YES`：

```bash
./scripts/restore-postgres.sh backups/shop-YYYYMMDDTHHMMSSZ.sql
```

## 首版范围

- 数码配件、桌面小电器、办公文具 3 个商品分类。
- 首版 6 个种子商品。
- 商品、购物车、模拟下单与订单查询。
- 所有主要页面可用的全局客服悬浮球。
- 商品/订单查询、售后知识、退款审批与转人工。

详细可行性、技术设计和每日学习记录由项目管理目录单独维护，不进入本代码仓库。
