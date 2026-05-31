
import json
import httpx
from dataclasses import asdict
from elasticsearch import AsyncElasticsearch
from app.entities.value_info import ValueInfo
from app.core.log import logger

class ValueESRepository:
    """负责字段取值全文索引的创建与批量写入"""

    index_name = "value_index"
    index_mappings = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_max_word",
            },
            "column_id": {"type": "keyword"},
        },
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def ensure_index(self):
        """确保字段取值索引已经创建好"""
        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(
                index=self.index_name,
                body={"mappings": self.index_mappings}  # 通过 body 传递，兼容性最佳
            )
            logger.info("索引创建成功")

    async def index(self, value_infos: list[ValueInfo], batch_size=20):
        """分批写入字段取值，避免一次 bulk 过大"""
        if not value_infos:
            return

        for i in range(0, len(value_infos), batch_size):
            batch = value_infos[i : i + batch_size]
            operations = []
            for v in batch:
                operations.append({"index": {"_index": self.index_name, "_id": v.id}})
                operations.append(asdict(v))
            await self.client.bulk(operations=operations)

        logger.info(f"成功写入 {len(value_infos)} 条字段取值到 ES")

    async def search(self, query: str, limit: int = 10) -> list[ValueInfo]:
        """根据关键词全文检索字段取值，返回 ValueInfo 列表"""
        body = {
            "query": {
                "match": {
                    "value": query  # 使用 value 字段进行 match 查询
                }
            },
            "size": limit
        }
        try:
            response = await self.client.search(index=self.index_name, body=body)
            hits = response["hits"]["hits"]
            result = []
            for hit in hits:
                source = hit["_source"]
                result.append(ValueInfo(
                    id=source["id"],
                    column_id=source["column_id"],
                    value=source["value"]
                ))
            return result
        except Exception as e:
            logger.error(f"ES 检索失败: {e}")
            return []