from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def fail(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """超过重试次数，返回失败信息"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "SQL校验失败", "status": "error"})
    error_msg = f"SQL 经过 {state.get('retry_count',0)} 次修正仍无法通过校验，请稍后重试。"
    logger.error(error_msg)
    writer({"type": "error", "message": error_msg})
    return {}