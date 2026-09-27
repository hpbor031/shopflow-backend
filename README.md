# ShopFlow Backend

电商交易平台后端，采用 `API → Service → CRUD → Database` 分层架构与全异步实现。

## 技术栈

| 分类 | 技术 |
| --- | --- |
| 语言 | Python 3.13 |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.x（异步 AsyncSession） |
| 数据库 | MySQL 8（驱动 aiomysql） |
| 数据校验 | Pydantic v2 |
| 认证 | JWT（PyJWT）+ bcrypt |
| 配置管理 | python-dotenv |
| 缓存 | Redis（规划中） |

## 已实现功能

- **用户注册**：用户名 / 邮箱唯一性校验，密码经 bcrypt 加盐哈希后入库（不存明文）
- **用户登录**：校验密码与账号状态后签发 JWT access_token
- **统一鉴权依赖**：`get_current_user` 解析 `Authorization: Bearer <token>`，校验签名、有效期与账号状态，供所有需要登录的接口复用
- **获取当前用户**：`GET /users/me`

## 目录结构

```
ShopFlow Backend/
├── main.py                 # 应用入口：lifespan 建表、挂载路由
└── app/
    ├── api/                # 接口层：路由与依赖（users.py、deps.py）
    ├── core/               # 基础设施：config.py 配置 / database.py 数据库 / security.py 密码与 JWT
    ├── models/             # SQLAlchemy ORM 模型（models.py，6 张表）
    ├── schemas/            # Pydantic 请求 / 响应模型
    ├── CRUD/               # 数据访问层：只负责数据库增删改查
    └── services/           # 业务逻辑层
```

## 快速开始

### 1. 环境准备

- Python 3.13、MySQL 8
- 创建数据库（表结构在服务启动时自动创建）：

```sql
CREATE DATABASE ShopFlow DEFAULT CHARSET utf8mb4;
```

### 2. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate                                    # Windows
source .venv/bin/activate                                 # macOS / Linux

pip install fastapi "uvicorn[standard]" "sqlalchemy>=2.0" aiomysql "pydantic[email]" PyJWT bcrypt python-dotenv
```

### 3. 配置环境变量

```bash
cp .env.example .env                                      # Windows: Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # 生成 SECRET_KEY 并写入 .env
```

`.env` 需要填写 MySQL 连接信息与 `SECRET_KEY`，字段说明见 `.env.example`。

### 4. 启动服务

```bash
python -m uvicorn main:app --reload
```

- 服务地址：http://127.0.0.1:8000
- 交互式文档：http://127.0.0.1:8000/docs（受保护接口可通过 Authorize 按钮粘贴 token 调试）

## 接口一览

| 方法 | 路径 | 说明 | 需要登录 |
| --- | --- | --- | --- |
| GET | `/` | 服务探活 | 否 |
| POST | `/users/register` | 用户注册 | 否 |
| POST | `/users/login` | 登录并获取 access_token | 否 |
| GET | `/users/me` | 获取当前登录用户信息 | 是 |

调用示例（Windows PowerShell）：

```powershell
# 注册
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/users/register -ContentType 'application/json' -Body '{"username":"hp01","email":"hp01@example.com","password":"abc123456"}'

# 登录并取出 token
$token = (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/users/login -ContentType 'application/json' -Body '{"username":"hp01","password":"abc123456"}').access_token

# 携带 token 访问受保护接口
Invoke-RestMethod -Uri http://127.0.0.1:8000/users/me -Headers @{ Authorization = "Bearer $token" }
```

## 数据表

| 表 | 说明 |
| --- | --- |
| `users` | 用户（密码只存 bcrypt 哈希，`status` 1=正常 0=禁用） |
| `categories` | 商品分类 |
| `products` | 商品（价格用定点数、库存、销量、上下架状态） |
| `cart_items` | 购物车明细（用户 × 商品 × 数量） |
| `orders` | 订单主表（总金额、订单状态） |
| `order_items` | 订单明细（下单时的商品名与单价快照，改价不影响历史订单） |

## 开发计划

- [x] 项目基础结构、MySQL 异步连接、配置与安全模块
- [x] 用户模块：注册 / 登录 / JWT 鉴权 / 获取当前用户
- [ ] 商品模块：分类、CRUD、搜索、分页、排序、库存
- [ ] 购物车模块
- [ ] 订单模块：库存校验与扣减、事务处理
- [ ] Redis 商品缓存
- [ ] 统一异常处理与日志
- [ ] Alembic 数据库迁移
- [ ] Docker / Docker Compose
- [ ] 自动化测试

## 协作规范

分支流程：`feature/功能名` → PR → `dev` → `main`。提交信息采用 Conventional Commits 风格，例如 `feat(user): 新增登录接口`。
