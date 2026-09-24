"""
安全工具模块（app/core/security.py）

本模块只负责两件事：
1. 密码安全：用 bcrypt 给密码做哈希、验密码（注册 / 登录）
2. 身份凭证：用 JWT 签发 access_token、校验 access_token（登录 / 访问受保护接口）

本模块不碰数据库、不写业务逻辑，只做纯函数式的加解密工作，
这样任何一层（service / api）都可以直接复用它。

==================== 一、JWT 是什么 ====================

JWT（JSON Web Token）是服务器签发给客户端的一张"电子入场券"。
HTTP 是无状态的，服务器不认识"上一个请求是谁发的"，所以需要客户端每次请求都带上凭证。
用 JWT 时服务器不保存登录状态，状态全写在 token 里，靠签名防止别人伪造。

一个 token 就是一个 "." 分隔的三段字符串：

    eyJhbGciOiJIUzI1NiJ9 . eyJzdWIiOiIxIiwiZXhwIjoxNzU4NjAwMDB9 . dBjftJeZ4CVP-mB92Xk
    └──── Header ① ────┘   └──────── Payload ② ──────────┘   └──── Signature ③ ────┘

    ① Header  ：算法信息 {"alg": "HS256", "typ": "JWT"}，固定写法
    ② Payload ：业务数据 {"sub": "1", "iat": ..., "exp": ...}
                ！注意：它只是 base64url 编码，不是加密！任何人复制到 jwt.io 都能解开看，
                 所以绝对不能放密码、手机号这类敏感信息
    ③ Signature：用服务器密钥 SECRET_KEY 对 ①② 做 HMAC-SHA256 算出来的签名
                ！它的唯一作用是防篡改：别人把 ② 里的 sub 改成别人的 id 想冒充该用户，
                 签名就对不上，服务器直接拒绝

结论：Payload 可读但不可篡改；SECRET_KEY 泄露 = 公章被盗 = 认证失效。

==================== 二、在本项目中的完整流程 ====================

注册：
    明文密码 --bcrypt.hashpw--> password_hash 存进 users 表
    （数据库里永远不存明文；bcrypt 每次自动生成随机"盐"，
      同一个密码两次哈希结果不同，可以有效防彩虹表攻击）

登录（签发 token）：POST /auth/login
    username + password
      → 按 username 查 users 表
      → bcrypt.checkpw 校验密码
      → jwt.encode({...}, SECRET_KEY) 签发 token
      → 返回给客户端 {"access_token": "...", "token_type": "bearer"}

访问受保护接口（校验 token）：GET /users/me
    请求头：Authorization: Bearer <token>
      → 取出 token
      → jwt.decode(token, SECRET_KEY, algorithms=["HS256"])：校验签名 + 是否过期
      → 通过后从 payload 拿到 user_id（即 sub）
      → 用 user_id 查库，返回当前用户

==================== 三、本模块依赖 ====================

bcrypt：单向哈希算法（只能加密、不能解密），专为存密码设计，自带随机盐
PyJWT ：JWT 的 Python 实现，提供 encode（签发）和 decode（校验）
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

# bcrypt 算法本身只处理密码的前 72 字节，超过部分会被忽略。
# 这里主动做长度校验，避免"用户以为设了超长密码、实际只有前 72 字节生效"的误会。
# 后续写 Pydantic 的注册 schema 时，也要限制 password 的最大长度。
BCRYPT_MAX_PASSWORD_BYTES: int = 72


# ==================== 密码哈希（bcrypt） ====================

def hash_password(password: str) -> str:
    """
    把明文密码哈希成可以存数据库的字符串（注册、改密码时使用）。

    步骤：
        1. 明文转 bytes（bcrypt 只吃 bytes）
        2. gensalt() 生成随机盐
        3. hashpw() 把"盐 + 密码"一起哈希
        4. 结果是 bytes，解码成 str 才能存进 VARCHAR 字段

    例：hash_password("123456")
        -> "$2b$12$KIXQmc3WW9nT4m4uJ0h0xO..."（每次结果都不同）
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"密码长度不能超过 {BCRYPT_MAX_PASSWORD_BYTES} 字节")

    salt = bcrypt.gensalt()  # 随机盐，让相同密码的哈希结果也不相同
    password_hash = bcrypt.hashpw(password_bytes, salt)
    return password_hash.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    校验"用户输入的明文密码"和"数据库里的哈希"是否匹配（登录时使用）。

    bcrypt.checkpw 会从 password_hash 中把当初的盐取出来，
    用同样的方式再算一遍，然后比较，所以不需要我们自己存盐。

    返回 True 表示密码正确，False 表示密码错误。
    注意：平时不要用 "==" 比较哈希，因为每次生成的盐不同，哈希字符串永远不相等；
         必须用 bcrypt.checkpw。
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        # 明文超长、或数据库里的哈希格式被人为改坏时，bcrypt 会抛异常。
        # 对上层统一表现为"密码错误"，不把底层异常暴露出去。
        return False


# ==================== JWT 签发与校验（PyJWT） ====================

def create_access_token(
    user_id: int,
    username: str | None = None,
    expires_minutes: int | None = None,
) -> str:
    """
    签发 access_token（登录成功后调用）。

    :param user_id: 用户 id，会作为 JWT 的 sub（subject：这张票属于谁）
    :param username: 可选，放进 payload 方便前端直接展示，省一次数据库查询
    :param expires_minutes: 可选，自定义有效期（分钟），不传则用配置里的 60 分钟

    payload 里用到的标准字段（字段名由 JWT 规范规定）：
        sub：subject，票据主体，这里放用户 id（规范要求必须是字符串）
        iat：issued at，签发时间
        exp：expiration，过期时间，PyJWT 校验时会自动检查它
    除标准字段外也可以加自定义字段（如这里的 username）。

    返回：三段式 token 字符串。
    """
    now = datetime.now(timezone.utc)  # 用 UTC 时间，避免服务器时区不同导致过期时间错乱
    expire_minutes = expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES

    payload: dict[str, Any] = {
        # str(user_id)：PyJWT 2.10 之后校验时会强制要求 sub 为字符串，
        # 直接传 int 会抛 InvalidSubjectError，这是个很容易踩的坑。
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    if username:
        payload["username"] = username  # 自定义字段，方便前端展示

    # encode 会把 payload 做 base64url 编码，再用 SECRET_KEY 算出签名，拼成三段式字符串。
    # PyJWT 会自动把 datetime 转成时间戳。
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    校验并解析 token，返回 payload 字典（访问受保护接口时调用）。

    校验内容（PyJWT 自动完成）：
        1. 签名是否正确（用 SECRET_KEY 重算一遍对比）→ 不对抛 InvalidSignatureError
        2. 是否已过期（比对 exp 与当前时间）        → 过期抛 ExpiredSignatureError
        3. alg 是否在白名单内（algorithms 参数）    → 不匹配抛 InvalidAlgorithmError
        4. sub 是否符合规范                        → 不合规抛 InvalidSubjectError
    以上异常都继承自 jwt.PyJWTError，API 层统一捕获它并返回 401 即可。

    :raises jwt.PyJWTError: 校验失败（伪造、过期、格式错误等）
    """
    # algorithms 必须显式传入！若留空，攻击者可以把 Header 里的 alg 改成 "none"，
    # 做一个没有签名的 token 来绕过校验（这是 JWT 的经典漏洞）。
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_user_id_from_token(token: str) -> int | None:
    """
    便捷函数：直接从 token 里取出 user_id；任何校验失败都返回 None。

    适合"登出"这类不区分失败原因的场景。
    如果要给用户返回具体提示（过期请重新登录 / token 非法），
    请改用 decode_token 并捕获 jwt.PyJWTError 的不同子类。
    """
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None


# ==================== 学习用演示（不影响业务代码） ====================
# 运行方式（项目根目录）：python -m app.core.security
# 建议先跑一遍看输出，再回头读上面的函数注释，会更好理解。
if __name__ == "__main__":
    import base64
    import json

    print("=" * 70)
    print("① 密码哈希：bcrypt 是单向的，数据库里只存哈希，不存明文")
    print("=" * 70)
    raw_password = "123456"
    hashed = hash_password(raw_password)
    print("明文密码      :", raw_password)
    print("存入数据库的值:", hashed)
    print("长度          :", len(hashed), "字符（所以 users.password_hash 要 VARCHAR(255)）")
    print("再哈希一次    :", hash_password(raw_password))
    print("↑ 两次结果不同，因为盐是随机的，但下面校验都能通过：")
    print("verify_password('123456') :", verify_password("123456", hashed))
    print("verify_password('000000') :", verify_password("000000", hashed))

    print()
    print("=" * 70)
    print("② 签发 token：登录成功后返回给客户端")
    print("=" * 70)
    token = create_access_token(user_id=1, username="hp")
    print("token =", token)
    header_segment, payload_segment, signature_segment = token.split(".")
    print()
    print("拆成三段：")
    print("  ① Header    =", header_segment)
    print("  ② Payload   =", payload_segment)
    print("  ③ Signature =", signature_segment)
    print()
    print("② 只是 base64url 编码，不是加密，谁都能解开看：")
    padded = payload_segment + "=" * (-len(payload_segment) % 4)  # 补齐 base64 的 = 填充
    print("  解码后 payload =", base64.urlsafe_b64decode(padded).decode("utf-8"))
    print("  PyJWT 也提供了不校验签名的读法：", jwt.decode(token, options={"verify_signature": False}))

    print()
    print("=" * 70)
    print("③ 校验 token：签名正确 → 拿到 payload，sub 就是 user_id")
    print("=" * 70)
    payload = decode_token(token)
    print("decode_token 结果 =", payload)
    print("user_id =", get_user_id_from_token(token))

    print()
    print("=" * 70)
    print("④ 篡改实验：把 payload 里的 sub 从 1 改成 2（冒充别人）")
    print("=" * 70)
    forged_payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "2", "exp": payload["exp"]}).encode("utf-8")
    ).decode("utf-8").rstrip("=")
    # 注意：签名段仍然用原来那个，没有重新签名
    forged_token = f"{header_segment}.{forged_payload}.{signature_segment}"
    print("伪造的 token =", forged_token)
    try:
        decode_token(forged_token)
        print("校验通过了？（不应该出现这一行）")
    except jwt.InvalidSignatureError as e:
        print("校验失败，异常类型 InvalidSignatureError：", e)
    print("结论：payload 虽然能被改，但签名对不上，服务器拒绝 → 这就是 JWT 防伪造的原理")

    print()
    print("=" * 70)
    print("⑤ 过期实验：签发一个 -1 分钟就过期的 token")
    print("=" * 70)
    expired_token = create_access_token(user_id=1, expires_minutes=-1)
    try:
        decode_token(expired_token)
        print("校验通过了？（不应该出现这一行）")
    except jwt.ExpiredSignatureError as e:
        print("校验失败，异常类型 ExpiredSignatureError：", e)
    print("结论：exp 由 PyJWT 自动比对，过期即失效，服务器不需要额外存储任何登录状态")

    print()
    print("=" * 70)
    print("⑥ 换密钥实验：模拟别人用自己的密钥签发 token")
    print("=" * 70)
    other_key_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=60)},
        # 换来一个不少于 32 字节的密钥，否则 PyJWT 会额外抛 InsecureKeyLengthWarning 警告
        "someone-elses-secret-key-0123456789",
        algorithm=ALGORITHM,
    )
    try:
        decode_token(other_key_token)
        print("校验通过了？（不应该出现这一行）")
    except jwt.InvalidSignatureError as e:
        print("校验失败，异常类型 InvalidSignatureError：", e)
    print("结论：SECRET_KEY 就是公章，泄露了别人就能签发合法 token，所以必须放 .env")


