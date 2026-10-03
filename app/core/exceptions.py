"""
统一异常处理模块（app/core/exceptions.py）

作用：把全项目的错误响应收敛成同一种 JSON 结构，并把「未预料的异常」记进日志。

要处理的三类错误：
1. HTTPException        —— 我们自己主动抛的业务错误（401 未登录、404 商品不存在、409 重复…）
2. RequestValidationError —— Pydantic 参数校验失败，FastAPI 默认返回 422
3. Exception            —— 其他所有没被捕获的异常，属于服务端 bug，返回 500

统一后的错误响应体（保留 FastAPI 原本的 detail 字段，另外补 code / path，
这样既不影响前端原来的解析方式，又多了一份统一的错误码和出错路径）：

    {
        "detail": "认证凭证无效或已过期",
        "code": 401,
        "path": "/users/me"
    }

参数校验失败时额外带 errors，指明具体是哪个字段不合法：

    {
        "detail": "请求参数校验失败",
        "code": 422,
        "path": "/users/register",
        "errors": [{"field": "body.password", "message": "String should have at least 6 characters"}]
    }

安全要点：500 的异常堆栈只写进日志文件，绝不返回给客户端
（堆栈会暴露项目路径、库版本、SQL 语句等信息，是攻击者很喜欢的线索）。
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import get_logger

logger = get_logger(__name__)


def _error_response(
    status_code: int,
    detail: Any,
    request: Request,
    errors: list[dict[str, str]] | None = None,
) -> JSONResponse:
    """按统一格式构造错误响应。"""
    content: dict[str, Any] = {
        "detail": detail,
        "code": status_code,
        "path": request.url.path,
    }
    if errors:
        content["errors"] = errors
    return JSONResponse(status_code=status_code, content=content)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    处理 HTTPException：401 / 403 / 404 / 409 等主动抛出的业务错误。

    注意注册的是 Starlette 的 HTTPException，它是 FastAPI HTTPException 的父类，
    注册一次就能同时兜住两者（含 FastAPI 内建的 404、405 等错误）。
    """
    return _error_response(exc.status_code, exc.detail, request)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    处理请求参数校验失败（FastAPI 默认 422）。

    原始错误信息是一串 Pydantic 结构体，这里挑出「字段 + 原因」两列，
    前端可以直接定位到哪个参数填错了。同时记一条 WARNING 日志。
    """
    errors = [
        {
            # loc 形如 ("body", "password")，拼成 body.password 方便前端显示
            "field": ".".join(str(part) for part in error.get("loc", [])),
            "message": error.get("msg", ""),
        }
        for error in exc.errors()
    ]
    logger.warning(
        "请求参数校验失败 %s %s | %s",
        request.method,
        request.url.path,
        errors,
    )
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "请求参数校验失败",
        request,
        errors=errors,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    兜底处理器：任何没被业务代码捕获的异常都在这里收尾。

    logger.exception 会把完整堆栈写进日志（排查用），
    返回给客户端的则只有一句话，不暴露内部细节。
    """
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "服务器内部错误",
        request,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    把上面三个处理器挂到 FastAPI 应用上，在 main.py 里调用一次。

    注册后，接口里抛 HTTPException 不用再手写响应体，
    统一由这里输出相同结构，前端只要写一套错误处理逻辑。
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
