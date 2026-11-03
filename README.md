# ShopFlow Backend

电商交易平台后端，采用 `API → Service → CRUD → Database` 分层架构与全异步实现，已通过 Docker Compose 完成容器化部署（应用容器 + MySQL 8 容器）。

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
| 部署 | Docker、Docker Compose v2 |
| 缓存 | Redis（规划中） |

## 已实现功能

### 用户模块

- **用户注册**：用户名 / 邮箱唯一性校验，密码经 bcrypt 加盐哈希后入库（不存明文）
- **用户登录**：校验密码与账号状态后签发 JWT access_token
- **统一鉴权依赖**：`get_current_user` 解析 `Authorization: Bearer <token>`，校验签名、有效期与账号状态，供所有需要登录的接口复用
- **获取当前用户**：`GET /users/me`
- **修改个人信息 / 修改密码**：`PATCH /users/me`、`PATCH /users/me/password`（改密码需带旧密码二次确认）

### 商品与分类模块

- **商品 CRUD**：创建 / 修改 / 下架（软删除，保留历史订单关联数据）
- **商品列表**：关键词搜索、分类筛选、状态筛选、排序（白名单字段）、分页
- **分类 CRUD**：新增 / 修改 / 删除，删除前校验分类下是否还有商品

### 购物车模块

- 添加商品（自动累加数量）、修改数量、删除单项、查询列表、清空
- 加购与改数量都会校验商品是否上架、库存是否充足

### 订单模块

- **创建订单**：由购物车结算，校验商品状态与库存 → 汇总金额 → 写订单主表与明细 → 扣库存 / 累加销量 → 清空购物车，全程在一个事务内，异常整体回滚
- **订单列表**：按用户分页查询（新订单在前，不含明细）
- **订单详情**：订单主表 + 明细（商品名与单价为下单时的快照，改价不影响历史订单）
- **订单状态修改**：内置状态机，非法流转返回 400；取消订单自动归还库存与销量

### 管理模块（需要管理员身份）

- **用户管理**：`GET /admin/users` 分页查看用户、`PATCH /admin/users/{id}/status` 启用 / 禁用
- **商品管理**：`GET /admin/products` 查看全量商品（含已下架）
- **订单管理**：`GET /admin/orders` 查看全部用户订单、`PATCH /admin/orders/{id}/status` 修改任意订单状态
- 权限通过 `get_current_admin` 依赖实现：未登录 401、非管理员 403

### 工程化

- **统一异常处理**：业务异常 / 参数校验失败 / 未捕获异常统一响应结构，500 堆栈只进日志不外泄
- **日志**：控制台 + `logs/shopflow.log`（5MB 轮转，保留 5 份），含请求日志中间件（方法 / 路径 / 状态码 / 耗时）
- **容器化部署**：`Dockerfile` + `compose.yaml`，一条命令拉起应用与 MySQL 8；MySQL 健康检查通过后才启动应用，数据库用命名卷持久化，`.dockerignore` 保证 `.env`、虚拟环境与日志不会打进镜像

## 目录结构

```
ShopFlow Backend/
├── main.py                 # 应用入口：日志初始化、lifespan 建表、异常处理器、请求日志中间件、挂载路由
├── Dockerfile              # 应用镜像：python:3.13-slim + 依赖 + 源码，uvicorn 监听 0.0.0.0:8000
├── compose.yaml            # 编排 app（由 Dockerfile 构建）+ mysql（mysql:8.0）两个服务
├── .dockerignore           # 构建镜像时排除 .git / .venv / .env / 日志，密钥不进镜像
├── .env.example            # 环境变量模板（复制为 .env 后填写）
├── requirements.txt        # 依赖清单（镜像构建与本地安装共用）
├── logs/                   # 运行日志（gitignore，不入库）
└── app/
    ├── api/                # 接口层：路由与依赖
    │   ├── deps.py         #   get_current_user（登录校验）/ get_current_admin（管理员校验）
    │   ├── users.py        #   用户注册、登录、个人信息、改密码
    │   ├── products.py     #   商品 CRUD 与列表
    │   ├── categories.py   #   分类 CRUD
    │   ├── cart.py         #   购物车
    │   ├── order.py        #   订单创建 / 查询 / 状态修改
    │   └── admin.py        #   管理端接口（用户 / 商品 / 订单管理）
    ├── core/               # 基础设施
    │   ├── config.py       #   配置（读取 .env）
    │   ├── database.py     #   异步引擎、会话依赖、建表
    │   ├── security.py     #   bcrypt 密码哈希、JWT 签发与校验
    │   ├── exceptions.py   #   统一异常处理器
    │   └── logger.py       #   日志配置
    ├── models/             # SQLAlchemy ORM 模型（models.py，6 张表）
    ├── schemas/            # Pydantic 请求 / 响应模型
    ├── CRUD/               # 数据访问层：只负责数据库增删改查
    └── services/           # 业务逻辑层（含 admin.py 管理端业务）
```

## 快速开始

两种方式任选其一：容器化部署（推荐，不用本地装 Python / MySQL）或本地开发环境（方便调试）。

### 方式一：Docker Compose（推荐）

前置条件：Docker Desktop（Windows / macOS）或 Docker Engine + Compose v2（Linux）。

**1. 准备 `.env`**

Compose 和应用容器都会读取项目根目录的 `.env`。可以直接复制 `.env.example` 再改，Docker 部署时按下表填写：

```dotenv
# 应用连库：容器内必须用服务名 mysql，不能用 localhost（localhost 指向容器自己）
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=shopflow_user
MYSQL_PASSWORD=你的应用账号密码
MYSQL_DATABASE=ShopFlow

# MySQL 容器初始化 + 健康检查使用（仅在数据卷首次初始化时生效）
MYSQL_ROOT_PASSWORD=你的root密码

SECRET_KEY=你的JWT密钥
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

`SECRET_KEY` 不能为空，否则应用启动即抛 `RuntimeError` 退出（见 `app/core/config.py`）。生成方式：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**2. 构建并启动**

```bash
docker compose up -d --build
```

首次执行会拉取 `mysql:8.0` 镜像并构建应用镜像；`shopflow-app` 会等 `shopflow-mysql` 健康检查（`mysqladmin ping`）通过后才启动。

**3. 验证**

```bash
docker compose ps                                # app / mysql 都是 Up，mysql 会显示 (healthy)
curl http://127.0.0.1:8000/                       # {"message":"ShopFlow Backend"}
```

- 服务地址：http://127.0.0.1:8000
- 交互式文档：http://127.0.0.1:8000/docs（受保护接口可通过 Authorize 按钮粘贴 token 调试）
- 宿主机上的数据库客户端请连 **127.0.0.1:3307**（容器内仍是 3306，映射见 `compose.yaml`）

**4. 停止 / 清理**

```bash
docker compose down        # 停止并删除容器，数据库数据仍保留在数据卷中
docker compose down -v     # 连数据卷一起删除（数据库清空，下次启动是空库，慎用）
```

更多命令、数据持久化与排错见下方 [Docker 部署](#docker-部署) 章节。

### 方式二：本地开发环境

#### 1. 环境准备

- Python 3.13、MySQL 8
- 创建数据库（表结构在服务启动时自动创建）：

```sql
CREATE DATABASE ShopFlow DEFAULT CHARSET utf8mb4;
```

#### 2. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate                                    # Windows
source .venv/bin/activate                                 # macOS / Linux

pip install fastapi "uvicorn[standard]" "sqlalchemy>=2.0" aiomysql "pydantic[email]" PyJWT bcrypt python-dotenv
```

#### 3. 配置环境变量

```bash
cp .env.example .env                                      # Windows: Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # 生成 SECRET_KEY 并写入 .env
```

`.env` 需要填写 MySQL 连接信息与 `SECRET_KEY`，字段说明见 `.env.example`。本地运行时 `MYSQL_HOST` 填 `localhost`（或 `127.0.0.1`）、`MYSQL_USER` 填本地 MySQL 账号（如 `root`）；Docker 部署的取值不同，见 [Docker 部署 → 环境变量](#环境变量)。

#### 4. 启动服务

```bash
python -m uvicorn main:app --reload
```

- 服务地址：http://127.0.0.1:8000
- 交互式文档：http://127.0.0.1:8000/docs（受保护接口可通过 Authorize 按钮粘贴 token 调试）

## Docker 部署

### 服务组成

| 服务 | 容器名 | 镜像 / 来源 | 端口映射 | 说明 |
| --- | --- | --- | --- | --- |
| `app` | `shopflow-app` | 由 `Dockerfile` 构建（`python:3.13-slim`） | `8000:8000` | FastAPI 应用，`uvicorn main:app --host 0.0.0.0 --port 8000` |
| `mysql` | `shopflow-mysql` | `mysql:8.0` | `3307:3306` | 数据库，数据存于命名卷 `mysql_data` |

- 两个服务在同一自建网络 `shopflow-network` 内，应用通过服务名 `mysql` 访问数据库
- 启动顺序：`app` 依赖 `mysql` 的 `service_healthy` 条件，MySQL 健康检查通过后才启动应用，避免"应用先起来、连库失败直接退出"
- `restart: unless-stopped`：容器异常退出或宿主机重启后自动拉起
- 应用容器的环境变量由 `env_file: .env` 在运行时注入；镜像内不含 `.env`（`.dockerignore` 已排除），密码与密钥不会被打进镜像层

### 环境变量

同一个 `.env` 会被两处使用：`docker compose` 自身做变量替换（`MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD`），应用容器再通过 `env_file` 读取，用来连数据库和签发 JWT。

| 变量 | Docker 部署 | 本地运行 | 说明 |
| --- | --- | --- | --- |
| `MYSQL_HOST` | `mysql` | `localhost` | 容器内写 `localhost` 会连到容器自己，连不上数据库 |
| `MYSQL_PORT` | `3306` | `3306` | 容器内网端口；宿主机客户端连容器库用 `3307` |
| `MYSQL_USER` | `shopflow_user` | `root` 或自建账号 | MySQL 容器首次初始化时自动创建该账号并授权访问 `ShopFlow` |
| `MYSQL_PASSWORD` | 同上账号的密码 | 本地 MySQL 密码 | 应用连库密码 |
| `MYSQL_DATABASE` | `ShopFlow` | `ShopFlow` | 容器首次初始化时自动建库 |
| `MYSQL_ROOT_PASSWORD` | 必填 | 不需要 | MySQL 容器初始化 + 健康检查（`mysqladmin ping`）使用 |
| `SECRET_KEY` | 必填 | 必填 | 为空则配置校验失败，应用启动报错退出 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | `60` | access_token 有效期（分钟） |

> 本地运行与 Docker 部署交替使用时，记得切换 `MYSQL_HOST` 和 `MYSQL_USER` / `MYSQL_PASSWORD`，否则会出现"应用连不上库"或 `Access denied`。

### 常用命令

| 目的 | 命令 |
| --- | --- |
| 后台启动 | `docker compose up -d` |
| 改代码 / 依赖后重新构建并启动 | `docker compose up -d --build` |
| 查看容器状态 | `docker compose ps` |
| 跟踪应用日志 | `docker compose logs -f app` |
| 只看最近 200 行 | `docker compose logs --tail 200 app` |
| 进入应用容器 | `docker exec -it shopflow-app bash` |
| 进入 MySQL 命令行 | `docker exec -it shopflow-mysql mysql -ushopflow_user -p ShopFlow` |
| 重启应用 | `docker compose restart app` |
| 停止（保留数据） | `docker compose down` |
| 停止并删除数据卷 | `docker compose down -v` |

### 数据持久化与日志

- 数据库文件在命名卷 `mysql_data`（挂载到容器内 `/var/lib/mysql`），`docker compose down`、重建容器都不会丢数据
- `docker compose down -v` 会连卷一起删除，下次启动是空库；表结构由应用启动时的 `create_all` 自动重建
- 应用日志写在容器内 `logs/shopflow.log`，目前未挂载到宿主机，**容器重建后日志随之丢失**。需要保留时给 `app` 服务加挂载：

```yaml
services:
  app:
    volumes:
      - ./logs:/app/logs
```

### 修改管理员账号

```bash
docker exec -it shopflow-mysql mysql -ushopflow_user -p ShopFlow -e "UPDATE users SET role = 2 WHERE username = 'hp01';"
```

与本地运行一致：`role` 1=普通用户、2=管理员。改完重新登录，该账号才能访问 `/admin/*`。

### 常见问题排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `shopflow-app` 反复重启，日志报 `配置缺失：.env 中未找到 SECRET_KEY` | `.env` 里没有 `SECRET_KEY` 或值为空 | 补上后执行 `docker compose up -d` |
| 日志报连不上数据库（`localhost:3306` 连接被拒） | `.env` 的 `MYSQL_HOST` 还是 `localhost` | 改成 `mysql` |
| `Access denied for user 'root'@...` | 沿用了本地 MySQL 的账号 | Docker 部署改用 `shopflow_user` + `MYSQL_PASSWORD` |
| `shopflow-mysql` 起不来，提示必须指定 root 密码 | `.env` 缺 `MYSQL_ROOT_PASSWORD` | 补上该项；数据卷已存在时初始化不会重跑，需 `docker compose down -v` 后重建 |
| `Bind for 0.0.0.0:3307 failed: port is already allocated` | 宿主机端口被占用 | 改 `compose.yaml` 的映射端口，例如 `"3308:3306"` |
| 宿主机已有本地 MySQL，想同时连容器库 | 3306 被本地占用，所以容器映射到 3307 | 客户端连 `127.0.0.1:3307` |
| 改了代码 / 依赖，容器里没生效 | 仍在用旧镜像（`COPY` 只在构建时执行） | `docker compose up -d --build` |
| 改了 `.env` 不生效 | 环境变量在容器创建时注入 | `docker compose up -d` 让容器按新配置重建 |

## 接口一览

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/` | 服务探活 | 公开 |
| POST | `/users/register` | 用户注册（201） | 公开 |
| POST | `/users/login` | 登录并获取 access_token | 公开 |
| GET | `/users/me` | 获取当前登录用户信息 | 登录 |
| PATCH | `/users/me` | 修改当前用户用户名 / 邮箱 | 登录 |
| PATCH | `/users/me/password` | 修改密码（需提供旧密码） | 登录 |
| GET | `/categories` | 分类列表 | 公开 |
| GET | `/categories/{category_id}` | 分类详情 | 公开 |
| POST | `/categories` | 新增分类 | 登录 |
| PUT | `/categories/{category_id}` | 修改分类 | 登录 |
| DELETE | `/categories/{category_id}` | 删除分类（分类下有商品时不可删） | 登录 |
| GET | `/products` | 商品列表（关键词、分类、状态筛选 + 排序 + 分页） | 公开 |
| GET | `/products/{product_id}` | 商品详情 | 公开 |
| POST | `/products` | 新增商品 | 登录 |
| PUT | `/products/{product_id}` | 修改商品 | 登录 |
| DELETE | `/products/{product_id}` | 下架商品（软删除，保留历史订单数据） | 登录 |
| GET | `/cart` | 购物车列表 | 登录 |
| POST | `/cart` | 加入购物车（已存在则累加数量） | 登录 |
| PUT | `/cart/{product_id}` | 修改购物车中该商品的数量 | 登录 |
| DELETE | `/cart/{product_id}` | 从购物车移除该商品 | 登录 |
| DELETE | `/cart` | 清空购物车 | 登录 |
| POST | `/orders` | 由购物车结算生成订单 | 登录 |
| GET | `/orders` | 我的订单列表（分页，不含明细） | 登录 |
| GET | `/orders/{order_id}` | 订单详情（含商品明细快照） | 登录 |
| PATCH | `/orders/{order_id}/status` | 修改本人订单状态 | 登录 |
| GET | `/admin/users` | 用户列表（分页） | 管理员 |
| PATCH | `/admin/users/{user_id}/status` | 启用 / 禁用用户 | 管理员 |
| GET | `/admin/products` | 商品列表（含已下架商品） | 管理员 |
| GET | `/admin/orders` | 全部用户订单列表（分页） | 管理员 |
| PATCH | `/admin/orders/{order_id}/status` | 修改任意订单状态 | 管理员 |

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
| `users` | 用户（密码只存 bcrypt 哈希；`status` 1=正常 0=禁用；`role` 1=普通用户 2=管理员） |
| `categories` | 商品分类 |
| `products` | 商品（价格用定点数、库存、销量、上下架状态） |
| `cart_items` | 购物车明细（用户 × 商品 × 数量） |
| `orders` | 订单主表（总金额、订单状态） |
| `order_items` | 订单明细（下单时的商品名与单价快照，改价不影响历史订单） |

## 订单状态说明

| 状态值 | 含义 |
| --- | --- |
| 1 | 待付款 |
| 2 | 已付款 |
| 3 | 已发货 |
| 4 | 已完成 |
| 5 | 已取消 |

允许的流转（状态机在 `app/services/order.py`）：

```
1 待付款 ──► 2 已付款 ──► 3 已发货 ──► 4 已完成
   │            │
   └────────────┴──► 5 已取消
```

- 待付款只能改成「已付款」或「已取消」
- 已付款只能改成「已发货」或「已取消」
- 已发货只能改成「已完成」（货已发出，不允许直接取消）
- 已完成 / 已取消是终态，不能再修改
- 其余流转一律返回 **400**，响应里会说明当前状态可以改成哪些状态
- 改成「已取消」时，会把订单明细中的商品数量归还库存并回退销量（销量不会变为负数），与下单时的扣减逻辑对称

用户端只能修改**自己的**订单（越权返回 404）；管理员用 `/admin/orders/{order_id}/status` 可修改任意订单，共用同一套状态机。

```powershell
# 取消订单（归还库存）
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8000/orders/1/status -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body '{"status":5}'
```

## 管理员账号

管理员不是注册出来的，需要在数据库里给账号打标记：

```sql
-- role：1=普通用户，2=管理员
UPDATE users SET role = 2 WHERE username = 'hp01';
```

之后用该账号登录即可访问 `/admin/*`；非管理员访问返回 **403**，账号被禁用返回 **403**（即使 token 未过期也立即失效）。

Docker 部署时在容器里执行即可（`shopflow_user` 对 `ShopFlow` 库有全部权限）：

```bash
docker exec -it shopflow-mysql mysql -ushopflow_user -p ShopFlow -e "UPDATE users SET role = 2 WHERE username = 'hp01';"
```

## 统一响应与错误处理

所有错误响应结构一致（见 `app/core/exceptions.py`）：

```json
{
  "detail": "库存不足",
  "code": 400,
  "path": "/orders",
  "errors": null
}
```

- `code` 与 HTTP 状态码一致，方便前端统一判断
- `path` 为出错请求的路径
- `errors` 只在参数校验失败（422）时返回，内容是 Pydantic 的字段级错误列表
- 未捕获异常统一返回 **500**，堆栈只写入日志，不返回给客户端

## 日志

- 日志同时输出到控制台和 `logs/shopflow.log`（Docker 部署时两者都在容器内，用 `docker compose logs -f app` 查看）
- 单文件超过 5MB 自动轮转，保留最近 5 份（`shopflow.log.1` …）
- 每个请求都会记录一条访问日志：方法、路径、状态码、耗时

## 数据库结构升级说明

启动时会用 `create_all` 建表，但它**不会**给已经存在的表补字段。若从旧版本升级，需手动执行：

```sql
ALTER TABLE users ADD COLUMN role INT NOT NULL DEFAULT 1 AFTER status;
```

新建数据库无需执行，`create_all` 会自动带上 `role` 字段。

## 开发计划

- [x] 项目基础结构、MySQL 异步连接、配置与安全模块
- [x] 用户模块：注册 / 登录 / JWT 鉴权 / 获取当前用户 / 修改资料与密码
- [x] 商品模块：分类、CRUD、搜索、分页、排序、库存
- [x] 购物车模块
- [x] 订单模块：库存校验与扣减、事务处理、订单状态机
- [x] 管理模块：用户管理、商品管理（含下架商品）、订单管理
- [x] 统一异常处理与日志
- [x] Docker / Docker Compose 部署（应用容器 + MySQL 8，含健康检查、数据卷持久化）
- [ ] Redis 商品缓存
- [ ] Alembic 数据库迁移
- [ ] 自动化测试

## 协作规范

分支流程：`main-dev-futhre/功能名` → PR → `dev` → `main`。提交信息采用 Conventional Commits 风格，例如 `feat(user): 新增登录接口`。
