"""
项目配置模块（app/core/config.py）

作用：把散落在代码里的配置项集中到一处，只在这里读 .env。

为什么必须集中：
1. 敏感信息（密钥、数据库密码）不能写死在代码里，否则提交到 Git 就泄露了
2. 部署到服务器时，只改 .env 就能生效，代码一行都不用动
3. 一个配置项只有一个来源，不会出现"数据库里读 A、代码里又写 B"的问题

"""

import os

from dotenv import load_dotenv

# 把项目根目录下 .env 文件里的键值对加载到"环境变量"中。
# 不调用这一行，下面的 os.getenv() 只能读到操作系统的环境变量，读不到 .env 的内容。
load_dotenv()

# ==================== JWT 配置 ====================

# SECRET_KEY：签发和校验 token 用的密钥，相当于公司的"公章"。
# - 签发 token 时用它计算签名
# - 校验 token 时用它重新计算签名，对比是否一致
# 一旦泄露，别人就能自己造出"合法"的 token 来冒充任何用户，所以必须放在 .env 里。
# 生成方式（在项目根目录执行）：
#   python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY: str = os.getenv("SECRET_KEY", "")

# 签名算法。HS256 = HMAC + SHA256，属于"对称加密"：
# 签发和校验用的是同一个密钥 SECRET_KEY（本项目用这种，最简单）。
# 另一种是 RS256 非对称算法（私钥签发、公钥校验），多用于多方系统，本项目不需要。
ALGORITHM: str = "HS256"

# access_token 的有效期（分钟）。超过这个时间，token 会被 PyJWT 判定为过期而失效。
# 有效期越短越安全（被偷了也很快失效），但也意味着用户要更频繁地重新登录。
# 电商项目一般 30~120 分钟，这里默认 60。
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# 启动时就检查密钥是否配置好，避免带着"空密钥"运行：
# 空密钥签出来的 token 任何人都能伪造，等于没有认证。
if not SECRET_KEY:
    raise RuntimeError(
        "配置缺失：.env 中未找到 SECRET_KEY。\n"
        '请在项目根目录执行：python -c "import secrets; print(secrets.token_urlsafe(32))"\n'
        "然后把生成的字符串以 SECRET_KEY=xxx 的形式写入 .env 文件。"
    )

# ==================== mysql 配置 ====================
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")