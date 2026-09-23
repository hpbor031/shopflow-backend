# ShopFlow 电商交易平台后端

## 1. 项目定位

项目名称：ShopFlow 电商交易平台

英文项目名：ShopFlow Backend

项目类型：电商交易平台后端

项目目标：

这是一个用于 Python 后端实习/秋招作品集的完整后端项目。

重点展示：

* Python 后端开发能力
* FastAPI
* SQLAlchemy ORM
* MySQL
* Redis
* JWT 身份认证
* Docker
* RESTful API
* 数据库事务
* 分页、搜索、排序
* 项目分层与工程化能力

项目不是简单的 CRUD 练习，而是一个具有完整业务流程的后端项目。

---

## 2. 固定技术栈

核心技术栈必须保持不变：

* Python 3.13
* FastAPI
* SQLAlchemy 2.x
* aiomysql
* MySQL 8
* Pydantic v2
* Redis
* JWT
* bcrypt
* Docker
* Docker Compose
* Git

数据库：

* MySQL 8

ORM：

* SQLAlchemy 2.x
* 使用异步 SQLAlchemy

MySQL 异步驱动：

* aiomysql

缓存：

* Redis

认证：

* JWT

密码：

* bcrypt

---

## 3. 项目核心功能

### 用户模块

* 用户注册
* 用户登录
* JWT 身份认证
* 获取当前用户
* 修改个人信息
* 修改密码
* 用户状态管理

### 商品模块

* 创建商品
* 修改商品
* 删除商品
* 商品详情
* 商品列表
* 商品搜索
* 商品分类
* 分页
* 排序
* 库存管理
* 销量统计

### 购物车模块

* 添加商品
* 查看购物车
* 修改商品数量
* 删除商品
* 清空购物车

### 订单模块

* 创建订单
* 查询订单
* 查询订单详情
* 修改订单状态
* 订单历史
* 商品库存校验
* 库存扣减
* 订单事务处理

### 管理模块

* 用户管理
* 商品管理
* 分类管理
* 订单管理

---

## 4. Redis 使用场景

Redis 不能为了技术栈展示而强行使用。

至少实现：

### 商品缓存

查询热门商品或商品详情时：

请求
↓
Redis
↓
缓存存在 → 返回缓存
↓
缓存不存在
↓
MySQL
↓
写入 Redis
↓
返回数据

缓存需要设置过期时间。

Redis 可以进一步用于：

* 热门商品缓存
* 验证码/临时数据
* 登录相关临时数据

---

## 5. JWT 使用场景

用户登录成功后：

用户名 + 密码
↓
查询 MySQL
↓
验证密码
↓
生成 JWT
↓
返回 access_token

访问需要认证的接口：

Authorization: Bearer <token>

FastAPI 通过 Depends 获取当前用户。

需要认证的接口不能直接允许未登录用户访问。

---

## 6. 数据库核心表

### users

字段：

* id
* username
* password_hash
* email
* status
* created_at
* updated_at

### categories

字段：

* id
* name
* created_at

### products

字段：

* id
* category_id
* name
* description
* price
* stock
* sales
* status
* created_at
* updated_at

### cart_items

字段：

* id
* user_id
* product_id
* quantity
* created_at

### orders

字段：

* id
* user_id
* total_amount
* status
* created_at
* updated_at

### order_items

字段：

* id
* order_id
* product_id
* product_name
* price
* quantity

---

## 7. 数据关系

User

→ CartItem

→ Product

User

→ Order

→ OrderItem

Category

→ Product

Order

→ OrderItem

---

## 8. 项目目录

最终目标结构：

ShopFlow Backend/

├── app/

│   ├── main.py

│   │

│   ├── core/

│   │   ├── config.py

│   │   ├── security.py

│   │   └── exceptions.py

│   │

│   ├── database/

│   │   ├── database.py

│   │   └── redis.py

│   │

│   ├── models/

│   │   ├── user.py

│   │   ├── product.py

│   │   ├── category.py

│   │   ├── cart.py

│   │   ├── order.py

│   │   └── order_item.py

│   │

│   ├── schemas/

│   │   ├── user.py

│   │   ├── product.py

│   │   ├── category.py

│   │   ├── cart.py

│   │   ├── order.py

│   │   └── common.py

│   │

│   ├── api/

│   │   ├── deps.py

│   │   ├── auth.py

│   │   ├── users.py

│   │   ├── products.py

│   │   ├── categories.py

│   │   ├── cart.py

│   │   └── orders.py

│   │

│   ├── services/

│   │   ├── auth_service.py

│   │   ├── user_service.py

│   │   ├── product_service.py

│   │   ├── cart_service.py

│   │   └── order_service.py

│   │

│   ├── crud/

│   │   ├── user.py

│   │   ├── product.py

│   │   ├── cart.py

│   │   └── order.py

│   │

│   └── utils/

│       ├── logger.py
│       └── response.py

├── tests/

├── alembic/

├── .env

├── .env.example

├── .gitignore

├── requirements.txt

├── Dockerfile

├── docker-compose.yml

├── PROJECT_SPEC.md

└── README.md

---

## 9. 分层架构

项目采用：

API → Service → CRUD → Database

API：

负责：

* 接收请求
* 参数验证
* 调用 Service
* 返回响应

Service：

负责：

* 核心业务逻辑
* 订单逻辑
* 库存逻辑
* 用户业务逻辑

CRUD：

负责：

* 数据库增删改查

Models：

负责：

* SQLAlchemy ORM 数据库映射

Schemas：

负责：

* Pydantic 请求/响应模型

Core：

负责：

* 配置
* JWT
* 安全
* 异常

Database：

负责：

* MySQL
* SQLAlchemy
* Redis

---

## 10. 核心业务流程

### 注册

客户端
↓
FastAPI
↓
Pydantic 校验
↓
检查用户名
↓
bcrypt 加密密码
↓
SQLAlchemy
↓
MySQL
↓
返回结果

### 登录

客户端
↓
FastAPI
↓
查询用户
↓
bcrypt 验证密码
↓
生成 JWT
↓
返回 Token

### 商品查询

客户端
↓
FastAPI
↓
Redis
↓
缓存命中 → 返回

缓存未命中
↓
MySQL
↓
写入 Redis
↓
返回

### 创建订单

客户端
↓
JWT 身份认证
↓
检查商品
↓
检查库存
↓
计算订单金额
↓
创建订单
↓
创建订单明细
↓
扣减库存
↓
事务提交
↓
返回订单

如果过程中发生异常：

Rollback

---

## 11. 开发原则

### 原则 1

不要随意修改项目定位。

项目始终是：

ShopFlow 电商交易平台后端。

### 原则 2

不要随意更换技术栈。

除非用户明确要求，否则不要：

* 更换 FastAPI
* 更换 SQLAlchemy
* 更换 MySQL
* 删除 Redis
* 删除 JWT
* 更换 Python
* 改成 Django
* 改成 Flask

### 原则 3

不要一次性生成整个项目。

项目采用逐步开发。

每完成一个模块：

1. 编写代码
2. 启动项目
3. 测试
4. 修复问题
5. 再进入下一个模块

### 原则 4

优先保证代码能够运行。

不要为了所谓“高级架构”增加没有实际作用的复杂代码。

### 原则 5

所有新增功能必须服务于电商业务。

不要为了展示技术强行加入无关功能。

### 原则 6

涉及数据库修改时，必须考虑：

* 主键
* 外键
* NULL
* 默认值
* 唯一约束
* 事务
* 数据一致性

### 原则 7

不要覆盖用户已有代码。

修改代码之前先读取当前文件内容。

如果需要大规模重构，必须先说明修改范围。

---

## 12. AI 协作规则

当其他 AI 接手这个项目时，必须：

1. 先阅读 PROJECT_SPEC.md
2. 理解当前项目结构
3. 不改变项目定位
4. 不擅自更换技术栈
5. 不擅自删除已有功能
6. 不擅自重构整个项目
7. 修改代码前先检查现有代码
8. 一次只完成当前任务
9. 修改后说明修改了哪些文件
10. 如果发现架构问题，先说明，不要直接大规模修改

如果用户没有要求，不要：

* 重写整个项目
* 修改数据库整体结构
* 删除已有模块
* 更换框架
* 添加无关技术
* 生成大量用户无法理解的代码

---

## 13. 当前开发阶段

当前阶段：

项目初始化。

已经完成：

* 创建项目目录
* 创建 `.venv`
* FastAPI 安装
* SQLAlchemy 安装
* aiomysql 安装

当前正在进行：

* 项目目录搭建
* 数据库配置
* FastAPI + SQLAlchemy + MySQL 基础连接

后续按照以下顺序开发：

1. 项目基础结构
2. MySQL + SQLAlchemy
3. User 用户模块
4. JWT 登录认证
5. Product 商品模块
6. Category 分类模块
7. Cart 购物车
8. Order 订单
9. Redis 缓存
10. 异常处理
11. 日志
12. Alembic 数据库迁移
13. Docker
14. 测试
15. README
16. 项目最终完善

---

## 14. AI 输出代码时的要求

代码必须：

* 使用 Python 3.13
* 使用异步 FastAPI
* 使用 SQLAlchemy 2.x
* 数据库操作使用 AsyncSession
* MySQL 使用 aiomysql
* Pydantic 使用 v2 写法
* 代码结构清晰
* 变量命名规范
* 不使用已经废弃的写法

解释代码时：

* 使用中文
* 解释执行流程
* 解释为什么这样设计
* 不只给代码不解释
* 不使用过度复杂的设计模式

---

## 15. 项目最终目标

最终项目应该能够展示：

Python 后端开发
+
FastAPI
+
SQLAlchemy
+
MySQL
+
Redis
+
JWT
+
Docker
+
事务
+
缓存
+
权限
+
完整业务流程

项目最终用于：

* GitHub 作品集
* Python 后端实习简历
* 秋招项目展示
* 面试项目讲解
