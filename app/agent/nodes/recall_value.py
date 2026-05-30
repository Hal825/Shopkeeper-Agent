"""
字段取值召回节点

负责从字段值全文索引中召回候选取值
当用户问题里出现店铺名 类目名 地区名等业务值时，这一步可以帮助定位真实字段和值
"""

import asyncio
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("召回字段取值")

    keywords = state.get("keywords", [])
    if not keywords:
        logger.warning("[recall_value] 没有关键词，跳过召回")
        return {"retrieved_value_infos": []}

    query_text = " ".join(keywords)
    value_repo = runtime.context["value_es_repository"]
    retrieved_values = await value_repo.search(query_text, limit=10)

    logger.info(f"[recall_value] 检索到 {len(retrieved_values)} 条字段取值信息")
    for v in retrieved_values[:5]:
        logger.info(f"  - {v.column_id}: {v.value}")

    return {"retrieved_value_infos": retrieved_values}