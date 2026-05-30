"""
字段召回节点

负责根据关键词从字段向量知识库中召回候选字段
它解决的是“用户问题可能对应哪些数据库字段”的问题
"""

import asyncio
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("召回字段信息")

    keywords = state.get("keywords", [])
    if not keywords:
        logger.warning("[recall_column] 没有关键词，跳过召回")
        return {"retrieved_column_infos": []}

    query_text = " ".join(keywords)
    embedding_client = runtime.context["embedding_client"]
    # 同步方法转异步
    embedding = await asyncio.to_thread(embedding_client.embed_query, query_text)

    column_repo = runtime.context["column_qdrant_repository"]
    retrieved_columns = await column_repo.search(
        embedding=embedding,
        score_threshold=0.6,
        limit=20
    )

    logger.info(f"[recall_column] 检索到 {len(retrieved_columns)} 条字段信息")
    for col in retrieved_columns[:5]:
        logger.info(f"  - {col.id}: {col.name}")

    return {"retrieved_column_infos": retrieved_columns}