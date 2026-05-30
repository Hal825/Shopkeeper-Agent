"""
指标召回节点

负责根据用户问题从指标向量知识库中召回候选指标
它帮助 Agent 把“销售额 转化率 客单价”等业务表达映射到已定义指标
"""

import asyncio
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("召回指标信息")

    keywords = state.get("keywords", [])
    if not keywords:
        logger.warning("[recall_metric] 没有关键词，跳过召回")
        return {"retrieved_metric_infos": []}

    query_text = " ".join(keywords)
    embedding_client = runtime.context["embedding_client"]
    embedding = await asyncio.to_thread(embedding_client.embed_query, query_text)

    metric_repo = runtime.context["metric_qdrant_repository"]
    retrieved_metrics = await metric_repo.search(
        embedding=embedding,
        score_threshold=0.6,
        limit=10
    )

    logger.info(f"[recall_metric] 检索到 {len(retrieved_metrics)} 条指标信息")
    for m in retrieved_metrics[:5]:
        logger.info(f"  - {m.id}: {m.name}")

    return {"retrieved_metric_infos": retrieved_metrics}