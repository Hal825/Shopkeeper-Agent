"""
请求上下文

用于保存和传递一次请求或一次脚本执行过程中的上下文变量，
当前先维护 request_id，后续日志模块会从这里读取 request_id 并注入到每条日志中
"""

from contextvars import ContextVar

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="1")