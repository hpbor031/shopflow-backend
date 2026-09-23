# ShopFlow Agent Rules

## 项目
- 项目名：ShopFlow Backend
- 定位：电商交易平台后端
- 技术栈：Python 3.13 + FastAPI + SQLAlchemy 2.x + MySQL 8 + Redis
- 架构：API → Service → CRUD → Database

## 核心规则
1. 不得擅自修改项目定位和技术栈
2. 不得擅自修改核心数据库设计
3. 不得删除已有功能
4. 修改代码前先检查现有项目结构
5. 优先复用已有代码，不重复造轮子
6. 每次只完成当前任务，不扩展无关功能
7. 修改数据库结构必须先说明
8. 修改依赖必须先说明
9. 完成后说明修改了哪些文件以及原因

## 当前阶段
正在开发 ShopFlow Backend。

## 开发原则
- 使用异步 FastAPI
- 使用 SQLAlchemy 2.x AsyncSession
- 数据库操作使用 ORM
- 敏感配置放 .env
- API / Service / CRUD 分层