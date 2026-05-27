# """
# 元数据知识构建服务
#
# 负责组织元数据知识库构建的核心业务流程，位于脚本入口和仓储层之间
# 一方面接收配置文件，另一方面协调元数据库和数仓查询仓储
#
# 向量索引，全文索引和指标构建逻辑后续再逐步补充
# """
# import asyncio
# import uuid
# from dataclasses import asdict
# from pathlib import Path
#
# from langchain_huggingface import HuggingFaceEndpointEmbeddings
# from omegaconf import OmegaConf
#
# from app.conf.meta_config import MetaConfig
# from app.core.log import logger
# from app.entities.column_info import ColumnInfo
# from app.entities.column_metric import ColumnMetric
# from app.entities.metric_info import MetricInfo
# from app.entities.table_info import TableInfo
# from app.entities.value_info import ValueInfo
# from app.repositories.es.value_es_repository import ValueESRepository
# from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
# from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
# from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
# from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
#
# class MetaKnowledgeService:
#     def __init__(
#             self,
#             meta_mysql_repository: MetaMySQLRepository,
#             dw_mysql_repository: DWMySQLRepository,
#             column_qdrant_repository: ColumnQdrantRepository,
#             embedding_client: HuggingFaceEndpointEmbeddings,
#             value_es_repository: ValueESRepository = None,  # 可选，当前不用
#             metric_qdrant_repository: MetricQdrantRepository = None,  # 可选
#     ):
#         self.meta_mysql_repository = meta_mysql_repository
#         self.dw_mysql_repository = dw_mysql_repository
#         self.column_qdrant_repository = column_qdrant_repository
#         self.embedding_client = embedding_client
#         self.value_es_repository = value_es_repository
#         self.metric_qdrant_repository = metric_qdrant_repository
#
#     async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfo]):
#         await self.column_qdrant_repository.ensure_collection()
#
#         batch_size = 1   # 你的环境内存很紧，批次可以小一点
#         batch_points = []
#
#         for column_info in column_infos:
#             text = f"""
# 字段名: {column_info.name}
# 业务含义: {column_info.description}
# 别名: {",".join(column_info.alias[:3])}
# 所属表: {column_info.table_id}
# 字段类型: {column_info.role}
# 示例值: {",".join(map(str, column_info.examples[:3]))}
# """.strip()
#
#             batch_points.append({
#                 "id": str(uuid.uuid4()),
#                 "embedding_text": text,
#                 "payload": asdict(column_info),
#             })
#
#             if len(batch_points) >= batch_size:
#                 await self._flush_column_batch(batch_points)
#                 batch_points.clear()
#
#         if batch_points:
#             await self._flush_column_batch(batch_points)
#
#     async def _flush_column_batch(self, batch_points):
#         texts = [p["embedding_text"] for p in batch_points]
#         ids = [p["id"] for p in batch_points]
#         payloads = [p["payload"] for p in batch_points]
#
#         # 这里直接调你本地的 embedding 服务
#         loop = asyncio.get_running_loop()
#         embeddings = await loop.run_in_executor(
#             None, self.embedding_client.embed_documents, texts
#         )
#
#         await self.column_qdrant_repository.upsert(ids, embeddings, payloads)
#
#     async def _save_tables_to_meta_db(self, meta_config: MetaConfig) -> list[ColumnInfo]:
#         table_infos: list[TableInfo] = []
#         column_infos: list[ColumnInfo] = []
#
#         for table in meta_config.tables:
#             table_info = TableInfo(
#                 id=table.name,
#                 name=table.name,
#                 role=table.role,
#                 description=table.description,
#             )
#             table_infos.append(table_info)
#
#             column_types = await self.dw_mysql_repository.get_column_types(table.name)
#             for column in table.columns:
#                 column_values = await self.dw_mysql_repository.get_column_values(
#                     table.name, column.name
#                 )
#                 column_info = ColumnInfo(
#                     id=f"{table.name}.{column.name}",
#                     name=column.name,
#                     type=column_types[column.name],
#                     role=column.role,
#                     examples=column_values,
#                     description=column.description,
#                     alias=column.alias,
#                     table_id=table.name,
#                 )
#                 column_infos.append(column_info)
#
#         async with self.meta_mysql_repository.session.begin():
#             self.meta_mysql_repository.save_table_infos(table_infos)
#             self.meta_mysql_repository.save_column_infos(column_infos)
#
#         return column_infos
#
#
#     async def _save_value_info_to_es(self, meta_config: MetaConfig, column_infos: list[ColumnInfo]):
#         await self.value_es_repository.ensure_index()
#
#         # 建立字段ID -> sync标志的映射
#         col_sync = {}
#         for table in meta_config.tables:
#             for col in table.columns:
#                 col_sync[f"{table.name}.{col.name}"] = col.sync
#
#         value_infos = []
#         for col_info in column_infos:
#             if col_sync.get(col_info.id, False):
#                 # 取大量真实值（limit 100000）
#                 values = await self.dw_mysql_repository.get_column_values(
#                     col_info.table_id, col_info.name, 100000
#                 )
#                 for v in values:
#                     value_infos.append(ValueInfo(
#                         id=f"{col_info.id}.{v}",
#                         value=v,
#                         column_id=col_info.id,
#                     ))
#
#         await self.value_es_repository.index(value_infos)
#
#     async def _save_metrics_to_meta_db(self, meta_config: MetaConfig) -> list[MetricInfo]:
#         metric_infos = []
#         column_metrics = []
#
#         for metric in meta_config.metrics:
#             m = MetricInfo(
#                 id=metric.name,
#                 name=metric.name,
#                 description=metric.description,
#                 relevant_columns=metric.relevant_columns,
#                 alias=metric.alias,
#             )
#             metric_infos.append(m)
#             for col in metric.relevant_columns:
#                 column_metrics.append(ColumnMetric(column_id=col, metric_id=metric.name))
#
#         async with self.meta_mysql_repository.session.begin():
#             self.meta_mysql_repository.save_metric_infos(metric_infos)
#             self.meta_mysql_repository.save_column_metrics(column_metrics)
#
#         return metric_infos
#
#     async def _save_metrics_to_qdrant(self, metric_infos: list[MetricInfo]):
#         await self.metric_qdrant_repository.ensure_collection()
#
#         points = []
#         for m in metric_infos:
#             points.append({"id": uuid.uuid4(), "embedding_text": m.name, "payload": asdict(m)})
#             points.append({"id": uuid.uuid4(), "embedding_text": m.description, "payload": asdict(m)})
#             for alias in m.alias:
#                 points.append({"id": uuid.uuid4(), "embedding_text": alias, "payload": asdict(m)})
#
#         texts = [p["embedding_text"] for p in points]
#         batch_size = 20
#         embeddings = []
#         for i in range(0, len(texts), batch_size):
#             batch = texts[i:i + batch_size]
#             batch_emb = await self.embedding_client.aembed_documents(batch)
#             embeddings.extend(batch_emb)
#
#         ids = [p["id"] for p in points]
#         payloads = [p["payload"] for p in points]
#         await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)
#
#     async def build(self, config_path: Path):
#         context = OmegaConf.load(config_path)
#         schema = OmegaConf.structured(MetaConfig)
#         meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
#
#         if meta_config.tables:
#             # 1. 入库 Meta MySQL
#             column_infos = await self._save_tables_to_meta_db(meta_config)
#             logger.info("保存表信息和字段信息到 Meta MySQL")
#             # 2. 构建向量索引
#             await self._save_column_info_to_qdrant(column_infos)
#             logger.info("为字段信息建立向量索引")
#             # 3. 全文索引暂时跳过（内存不足）
#             # if self.value_es_repository and meta_config.enable_es:
#             #     await self._save_value_info_to_es(meta_config, column_infos)
#             #     logger.info("为字段取值建立全文索引")
#
#         if meta_config.metrics:
#             logger.info("检测到 metrics 配置，暂不处理")
#             # 等以后补充
#             # metric_infos = await self._save_metrics_to_meta_db(meta_config)
#             # await self._save_metrics_to_qdrant(metric_infos)




"""
元数据知识构建服务（完整版，可直接替换）

负责组织元数据知识库构建的核心业务流程，位于脚本入口和仓储层之间。
当前主线覆盖：
- 表字段入库
- 字段向量索引（拆分语义入口）
- 字段取值全文索引（可选，依赖 ES）
- 指标入库
- 指标向量索引
"""

import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Optional
from sqlalchemy import text

from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    """负责串联元数据知识库构建流程的应用服务"""

    def __init__(
        self,
        meta_mysql_repository: MetaMySQLRepository,
        dw_mysql_repository: DWMySQLRepository,
        column_qdrant_repository: ColumnQdrantRepository,
        embedding_client,  # 实际是 HuggingFaceEmbeddings，通过异步封装调用
        value_es_repository: Optional[ValueESRepository] = None,
        metric_qdrant_repository: Optional[MetricQdrantRepository] = None,
    ):
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    # ========== 表与字段入库 ==========
    async def _save_tables_to_meta_db(self, meta_config: MetaConfig) -> list[ColumnInfo]:
        table_infos: list[TableInfo] = []
        column_infos: list[ColumnInfo] = []

        for table in meta_config.tables:
            table_info = TableInfo(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            )
            table_infos.append(table_info)

            column_types = await self.dw_mysql_repository.get_column_types(table.name)

            for column in table.columns:
                column_values = await self.dw_mysql_repository.get_column_values(
                    table.name, column.name
                )
                column_info = ColumnInfo(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name,
                )
                column_infos.append(column_info)

        # 清空旧数据，避免主键冲突
        session = self.meta_mysql_repository.session
        await session.execute(text("DELETE FROM column_info"))
        await session.execute(text("DELETE FROM table_info"))
        await session.commit()

        async with self.meta_mysql_repository.session.begin():
            self.meta_mysql_repository.save_table_infos(table_infos)
            self.meta_mysql_repository.save_column_infos(column_infos)

        return column_infos

    # ========== 字段向量索引（拆点模式，提高召回率） ==========
    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfo]):
        await self.column_qdrant_repository.ensure_collection()

        points: list[dict] = []
        for col in column_infos:
            # 拆成多条语义入口：字段名、描述、别名各为一个点
            points.append({
                "id": str(uuid.uuid4()),
                "embedding_text": col.name,
                "payload": asdict(col),
            })
            points.append({
                "id": str(uuid.uuid4()),
                "embedding_text": col.description,
                "payload": asdict(col),
            })
            for alia in col.alias:
                points.append({
                    "id": str(uuid.uuid4()),
                    "embedding_text": alia,
                    "payload": asdict(col),
                })

        # 分批向量化
        texts = [p["embedding_text"] for p in points]
        batch_size = 20
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_emb = await self.embedding_client.aembed_documents(batch)
            embeddings.extend(batch_emb)

        ids = [p["id"] for p in points]
        payloads = [p["payload"] for p in points]
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)

    # ========== ES 全文索引（可选） ==========
    async def _save_value_info_to_es(self, meta_config: MetaConfig, column_infos: list[ColumnInfo]):
        if not self.value_es_repository:
            logger.info("ValueESRepository 未配置，跳过全文索引")
            return

        try:
            await self.value_es_repository.ensure_index()
        except Exception as e:
            logger.warning(f"Elasticsearch 不可用，跳过全文索引: {e}")
            return

        # 建立字段ID -> sync标志的映射
        col_sync = {}
        for table in meta_config.tables:
            for col in table.columns:
                col_sync[f"{table.name}.{col.name}"] = col.sync

        value_infos = []
        for col_info in column_infos:
            if col_sync.get(col_info.id, False):
                try:
                    values = await self.dw_mysql_repository.get_column_values(
                        col_info.table_id, col_info.name, 100000
                    )
                except Exception:
                    continue
                for v in values:
                    value_infos.append(ValueInfo(
                        id=f"{col_info.id}.{v}",
                        value=v,
                        column_id=col_info.id,
                    ))

        # 写入 ES（内部已用 httpx 解决版本兼容问题）
        try:
            await self.value_es_repository.index(value_infos)
            logger.info(f"全文索引写入成功，共 {len(value_infos)} 条")
        except Exception as e:
            logger.warning(f"全文索引写入失败: {e}")

    # ========== 指标入库 ==========
    async def _save_metrics_to_meta_db(self, meta_config: MetaConfig) -> list[MetricInfo]:
        metric_infos = []
        column_metrics = []

        for metric in meta_config.metrics:
            m = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias,
            )
            metric_infos.append(m)
            for col in metric.relevant_columns:
                column_metrics.append(ColumnMetric(column_id=col, metric_id=metric.name))

        # 清空旧数据
        session = self.meta_mysql_repository.session
        await session.execute(text("DELETE FROM column_metric"))
        await session.execute(text("DELETE FROM metric_info"))
        await session.commit()

        async with self.meta_mysql_repository.session.begin():
            self.meta_mysql_repository.save_metric_infos(metric_infos)
            self.meta_mysql_repository.save_column_metrics(column_metrics)

        return metric_infos

    # ========== 指标向量索引 ==========
    async def _save_metrics_to_qdrant(self, metric_infos: list[MetricInfo]):
        if not self.metric_qdrant_repository:
            logger.info("MetricQdrantRepository 未配置，跳过指标向量索引")
            return

        await self.metric_qdrant_repository.ensure_collection()

        points = []
        for m in metric_infos:
            points.append({
                "id": str(uuid.uuid4()),
                "embedding_text": m.name,
                "payload": asdict(m),
            })
            points.append({
                "id": str(uuid.uuid4()),
                "embedding_text": m.description,
                "payload": asdict(m),
            })
            for alias in m.alias:
                points.append({
                    "id": str(uuid.uuid4()),
                    "embedding_text": alias,
                    "payload": asdict(m),
                })

        texts = [p["embedding_text"] for p in points]
        batch_size = 20
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_emb = await self.embedding_client.aembed_documents(batch)
            embeddings.extend(batch_emb)

        ids = [p["id"] for p in points]
        payloads = [p["payload"] for p in points]
        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)

    # ========== 总控构建 ==========
    async def build(self, config_path: Path):
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(MetaConfig)
        meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))

        if meta_config.tables:
            column_infos = await self._save_tables_to_meta_db(meta_config)
            logger.info("表字段信息已保存到 Meta MySQL")

            await self._save_column_info_to_qdrant(column_infos)
            logger.info("字段向量索引构建完成")

            await self._save_value_info_to_es(meta_config, column_infos)
            logger.info("字段取值全文索引处理完成（如已启用）")

        if meta_config.metrics:
            metric_infos = await self._save_metrics_to_meta_db(meta_config)
            logger.info("指标信息已保存到 Meta MySQL")

            await self._save_metrics_to_qdrant(metric_infos)
            logger.info("指标向量索引构建完成")