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


