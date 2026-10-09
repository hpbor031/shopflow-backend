from datetime import datetime

from pydantic import BaseModel, Field, EmailStr,field_validator
# 用户模型
class UserBase(BaseModel):
    username: str = Field(...,min_length=3, max_length=50, title="用户名", description="用户名")
    email: EmailStr = Field(..., title="邮箱", description="邮箱")
# 用户创建,把密码单独拿出来
class UserCreate(UserBase):
    password: str = Field(...,min_length=6, max_length=50, title="密码", description="密码")
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        'password 字段的自定义校验函数，让 Pydantic 在验证 password 时自动调用它'
        if len(v.encode('utf-8')) > 72:
            raise ValueError('密码字节数不能多于72')
        return v

class UserUpdate(BaseModel):
    '''
    修改个人信息（PATCH /users/me）的请求体。

    两个字段全部可选，含义是"局部更新"（PATCH 的语义）：
    - 不传某个字段，或显式传 null → 该字段保持原样，不做修改
    - 传了才做格式校验（长度 / 邮箱格式），并参与唯一性判重
    这里故意不继承 UserBase：UserBase 的字段都是必填（...），
    而本模型需要每个字段都可选，单独声明比覆盖父类字段更清楚。
    '''
    username: str | None = Field(None, min_length=3, max_length=50, title="用户名", description="用户名，不传表示不修改")
    email: EmailStr | None = Field(None, title="邮箱", description="邮箱，不传表示不修改")

class register_response(BaseModel):
    '''
    注册响应,隐藏password_hash字段
    :param id: 用户id
    :param username: 用户名
    :param email: 邮箱
    :param status: 状态
    '''
    id: int = Field(..., title="用户id", description="用户id")
    username: str = Field(...,min_length=3, max_length=50, title="用户名", description="用户名")
    email: EmailStr = Field(..., title="邮箱", description="邮箱")
    status : int = Field(..., title="状态", description="状态")
class UserLogin(BaseModel):
    '''
    用户登录
    :param username: 用户名
    :param password: 密码
    '''
    username: str = Field(...,min_length=3, max_length=50, title="用户名", description="用户名")
    # 登录的密码故意不做 min_length / max_length / 强度校验：
    # 一是规则一旦演进（例如以后注册要求"必须含特殊字符"），老用户会在登录时被 422 挡住；
    # 二是密码对不对由 bcrypt 比对决定，输错了统一返回 401，不需要在这里拦。
    password: str = Field(..., title="密码", description="密码")

class TokenResponse(BaseModel):
    '''
    登录成功的响应：访问令牌
    :param access_token: JWT 字符串，客户端后续请求放在请求头 Authorization: Bearer <token>
    :param token_type: 令牌类型，固定为 bearer
    '''
    access_token: str = Field(...,title="访问令牌", description="JWT 字符串")
    token_type: str = Field(default="bearer", title="令牌类型", description="固定为 bearer")

class UserMeResponse(BaseModel):
    '''
    获取当前登录用户信息的响应。
    这里逐字段显式声明，相当于给响应体加了一份白名单：
    没有声明的字段（尤其是 password_hash）永远不会被序列化返回。
    :param id: 用户id
    :param username: 用户名
    :param email: 邮箱
    :param status: 状态
    :param created_at: 注册时间
    '''
    id: int = Field(..., title="用户id", description="用户id")
    username: str = Field(...,min_length=3, max_length=50, title="用户名", description="用户名")
    email: EmailStr = Field(..., title="邮箱", description="邮箱")
    status: int = Field(..., title="状态", description="状态")
    role: int = Field(..., title="角色", description="1=普通用户 2=管理员")
    created_at: datetime = Field(..., title="注册时间", description="注册时间")

class PasswordUpdate(BaseModel):
    '''
    修改密码（PATCH /users/me/password）的请求体。
    必须同时提供旧密码，做一次二次身份确认，避免 token 泄露后被人直接改掉密码。
    :param old_password: 旧密码
    :param new_password: 新密码
    '''
    old_password: str = Field(..., title="旧密码", description="旧密码")
    new_password: str = Field(...,min_length=6, max_length=50, title="新密码", description="新密码")
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        'new_password 字段的自定义校验函数：bcrypt 只处理前 72 字节，这里限制字节数'
        if len(v.encode('utf-8')) > 72:
            raise ValueError('密码字节数不能多于72')
        return v


class UserStatusUpdate(BaseModel):
    '''
    管理员修改用户状态（PATCH /admin/users/{user_id}/status）的请求体。

    :param status: 1=正常（可登录）0=禁用（持有合法 token 也会被拒绝）
    '''
    status: int = Field(..., ge=0, le=1, title="用户状态", description="1=正常 0=禁用")


