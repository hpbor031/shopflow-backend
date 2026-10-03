"""
接口依赖模块（app/api/deps.py）

作用：把"多个接口都要做的公共前置动作"抽成 FastAPI 的依赖（Depends），
     谁需要就在参数里写 Depends(get_current_user)，不用每个接口重复解析 token。

本模块的核心是 get_current_user：从请求头 Authorization: Bearer <token>
解析出"当前登录用户"。它相当于一道门禁，需要登录的接口在参数里写上它，
未携带合法 token 的请求会在进入接口函数体之前就被拦下。

执行顺序：
    ① HTTPBearer 从请求头取出 token
    ② decode_token 校验签名与有效期（失败 → 401）
    ③ 从 payload 的 sub 取出 user_id
    ④ 按 id 查 users 表（查不到 → 401，用户已被删除）
    ⑤ 校验 status（被禁用 → 403）
    ⑥ 把 User 对象注入到接口参数 current_user
"""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.user import get_user_by_id
from app.core.database import get_session
from app.core.security import decode_token
from app.models.models import ROLE_ADMIN, User

# HTTPBearer：声明本项目的认证方式是"请求头里带 Bearer token"。
# 创建一个“Bearer Token 提取器”
# auto_error=False：请求头缺失或不是 Bearer 格式时，不让 FastAPI 自动抛 403，
# 而是交回 None，由下面的函数统一按 401 处理，保证"未登录"的错误信息一致。
bearer_scheme = HTTPBearer(auto_error=False)
'''经过HTTPBearer()创建的bearer_scheme会返回一个包含scheme和credentials的HTTPAuthorizationCredentials对象
HTTPAuthorizationCredentials(
    scheme="Bearer", 认证方式
    credentials="abc123" 真正的JWT token
)
'''
# 401 响应按 HTTP 规范应带上 WWW-Authenticate 头，告诉客户端该用什么方式认证
_UNAUTHORIZED_HEADERS: dict[str, str] = {"WWW-Authenticate": "Bearer"}


async def get_current_user(
    #每次请求进入 get_current_user()，让 bearer_scheme 帮我从请求头拿认证信息，并把结果放进 credentials类
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    从请求头 Authorization: Bearer <token> 解析出当前登录用户。

    认证失败和"密码错误"一样，不告诉前端具体失败原因（缺 token / 签名错 / 过期 / 用户不存在
    统统是 401），避免给攻击者提供猜测信息。

    :return: ORM 的 User 对象，接口里可直接使用 current_user.id / username / status
    :raises HTTPException 401: 未带 token、token 非法或过期、token 对应用户不存在
    :raises HTTPException 403: 用户存在但已被禁用（status = 0）
    """
    # ① 请求头里没有 Authorization，或格式不是 Bearer xxx
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="未提供认证凭证",
            headers=_UNAUTHORIZED_HEADERS,
        )

    # ② 校验签名与有效期，并取出用户 id
    #    jwt.PyJWTError 覆盖了签名错误、已过期、格式非法等所有校验失败情况；
    #    KeyError / ValueError 兜住"token 合法但没有 sub 或 sub 不是数字"的异常数据。
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])  # 签发时写入的是 str(user_id)，这里转回 int
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="认证凭证无效或已过期",
            headers=_UNAUTHORIZED_HEADERS,
        )

    # ③ 按 id 查库：token 没到期不代表用户还在（可能已被删除）
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="认证凭证无效或已过期",
            headers=_UNAUTHORIZED_HEADERS,
        )

    # ④ 账号状态检查：被禁用的账号即使持有合法 token 也不允许访问
    if user.status == 0:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    管理员门禁：在「已登录」的基础上再校验角色。

    需要管理员权限的接口这样写：
        current_admin: User = Depends(get_current_admin)

    执行顺序：
        ① 先由 get_current_user 完成登录校验（未登录 / token 非法 / 账号被禁用在这里就被拦下）
        ② 再判断 role 是否为管理员，不是则 403

    :return: ORM 的 User 对象（当前管理员）
    :raises HTTPException 401: 未登录或 token 无效（由 get_current_user 抛出）
    :raises HTTPException 403: 已登录但不是管理员，或账号被禁用
    """
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    return current_user
