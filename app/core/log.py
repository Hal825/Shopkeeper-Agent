import sys
from pathlib import Path

from loguru import logger

from app.core.context import request_id_ctx_var

# 统一日志格式：时间、级别、request_id、位置、消息
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def inject_request_id(record):
    """从上下文变量中提取 request_id 注入到日志记录的 extra 字段"""
    record["extra"]["request_id"] = request_id_ctx_var.get()


# 移除 Loguru 默认的处理器（避免重复输出）
logger.remove()

# 注入 request_id 处理函数
logger = logger.patch(inject_request_id)

# ===== 1. 控制台输出（便于开发调试） =====
logger.add(
    sink=sys.stdout,
    format=log_format,
    level="INFO",          # 控制台只显示 INFO 及以上级别
    colorize=True,         # 终端彩色输出
)

# ===== 2. 文件输出（持久化存储） =====
# 定义日志目录和文件路径
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)   # 确保目录存在
log_file = log_dir / "app.log"

logger.add(
    sink=log_file,
    format=log_format,
    level="DEBUG",         # 文件记录 DEBUG 及以上级别（更详细）
    rotation="10 MB",      # 单个文件超过 10MB 则轮转
    retention="7 days",    # 保留最近 7 天的日志文件
    encoding="utf-8",
    enqueue=True,          # 异步写入，避免阻塞主线程
)