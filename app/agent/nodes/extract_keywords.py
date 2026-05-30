"""
关键词抽取节点

负责从用户自然语言问题中识别检索线索
后续字段召回 字段取值召回和指标召回都会基于这些关键词展开
"""

import asyncio
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("抽取关键词")

    query = state.get("query", "")
    # 简单策略：将原始问题作为关键词，也可拆分或调用 LLM
    keywords = [query]
    logger.info(f"[extract_keywords] 原始 query: {query}")
    logger.info(f"[extract_keywords] 提取的关键词: {keywords}")

    await asyncio.sleep(0.1)  # 占位耗时，可移除
    return {"keywords": keywords}