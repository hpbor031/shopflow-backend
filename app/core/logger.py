"""
日志模块（app/core/logger.py）

作用：给全项目提供统一的日志出口，替代散落在各处的 print。

为什么要统一：
1. print 只能打控制台，服务部署后日志没人看得到；写进文件才能事后排查问题
2. 出问题时需要知道「什么时候、哪个模块、什么级别」，这些信息由 Formatter 统一加
3. 一个配置函数定好规则，其他模块只写 logger.info(...) 即可

用法：
    在应用入口调用一次 setup_logging()，
    其他模块 `from app.core.logger import get_logger` 后 get_logger(__name__) 拿 logger。

日志同时输出到两处：
- 控制台：开发时直接看
- logs/shopflow.log：按大小自动轮转，避免日志文件无限增大
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 日志目录：logger.py 在 app/core/ 下，parents[2] 就是项目根目录
LOG_DIR: Path = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE: Path = LOG_DIR / "shopflow.log"

# 日志格式：时间 | 级别 | 模块名 | 内容
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """
    配置根 logger：同时输出到控制台和按大小滚动的日志文件。

    只需在 main.py 里调用一次；重复调用不会重复添加 handler
    （uvicorn --reload 会重新加载模块，不加判断会出现同样的日志打印两遍）。

    :param level: 日志级别，默认 INFO（DEBUG 及以上都会输出）
    """
    root = logging.getLogger()

    # 已经初始化过就直接返回，避免重复挂 handler 导致日志翻倍
    if any(getattr(handler, "_shopflow_handler", False) for handler in root.handlers):
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 单个文件最大 5MB，保留 5 个备份：shopflow.log.1 / .2 ...
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # 打个标记，下次调用时用它判断「这几个 handler 是本模块加的」
    for handler in (console_handler, file_handler):
        setattr(handler, "_shopflow_handler", True)

    root.setLevel(level)
    root.addHandler(console_handler)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    按模块名取 logger，约定写法：logger = get_logger(__name__)。

    这样日志里的「模块名」就是出错的文件，定位问题不用猜。
    """
    return logging.getLogger(name)
