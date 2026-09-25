from pydantic import BaseModel, Field, EmailStr
# 用户模型
class UserBase(BaseModel):
    username: str = Field(...,min_length=3, max_length=50, title="用户名", description="用户名")
    email: EmailStr = Field(..., title="邮箱", description="邮箱")
# 用户创建,把密码单独拿出来
class UserCreate(UserBase):
    password: str = Field(...,min_length=6, max_length=50, title="密码", description="密码")
