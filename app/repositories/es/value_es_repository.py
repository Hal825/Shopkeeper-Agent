# """
# 字段取值 ES 仓储
#
# 把字段真实取值组织成Elasticsearch 全文索引，并提供最小的索引创建与批量写入能力
#
# Service 层负责决定哪些字段需要同步
# Repository 只关心索引是否存在以及这些 ValueInfo 应该如何写进 ES
# """
#
# from dataclasses import asdict
#
# from elasticsearch import AsyncElasticsearch
#
# from app.entities.value_info import ValueInfo
#
#
# class ValueESRepository:
#     """负责字段取值全文索引的创建与批量写入"""
#
#     index_name = "value_index"
#     # value 字段使用 IK 分词，这样地区 会员等级 品类等中文值才能按全文方式检索
#     index_mappings = {
#         "dynamic": False,
#         "properties": {
#             "id": {"type": "keyword"},
#             "value": {
#                 "type": "text",
#                 "analyzer": "ik_max_word",
#                 "search_analyzer": "ik_max_word",
#             },
#             "column_id": {"type": "keyword"},
#         },
#     }
#
#     def __init__(self, client: AsyncElasticsearch):
#         self.client = client
#
#     async def ensure_index(self):
#         """确保字段取值索引已经创建好（使用底层 API 避免 400）"""
#         if not await self.client.indices.exists(index=self.index_name):
#             # 直接发送 PUT 请求，完全复制成功的 curl 命令
#             await self.client.transport.perform_request(
#                 "PUT",
#                 f"/{self.index_name}",
#                 body={"mappings": self.index_mappings},
#                 headers={"Content-Type": "application/json"},
#             )
#
#     async def index(self, value_infos: list[ValueInfo], batch_size=20):
#         """分批写入字段取值，避免一次 bulk 过大"""
#         if not value_infos:
#             return
#
#         for i in range(0, len(value_infos), batch_size):
#             batch_value_infos = value_infos[i : i + batch_size]
#             batch_operations = []
#             for value_info in batch_value_infos:
#                 # 用 ValueInfo.id 作为文档 id，这样重复构建时会覆盖同一条值记录
#                 batch_operations.append(
#                     {"index": {"_index": self.index_name, "_id": value_info.id}}
#                 )
#                 batch_operations.append(asdict(value_info))
#             await self.client.bulk(operations=batch_operations)



import json
import httpx
from dataclasses import asdict
from elasticsearch import AsyncElasticsearch
from app.entities.value_info import ValueInfo
from app.core.log import logger

class ValueESRepository:
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
        # 使用 httpx 确保索引存在
        url = f"http://localhost:9200/{self.index_name}"
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.head(url)
            if resp.status_code == 404:
                create_resp = await http_client.put(
                    url,
                    json={"mappings": self.index_mappings}
                )
                if create_resp.status_code not in (200, 201):
                    raise Exception(f"创建索引失败: {create_resp.status_code} {create_resp.text}")

    async def index(self, value_infos: list[ValueInfo], batch_size=20):
        """使用 httpx 发送 bulk 请求，避免 elasticsearch-py 版本冲突"""
        if not value_infos:
            return

        for i in range(0, len(value_infos), batch_size):
            batch = value_infos[i : i + batch_size]
            # 构造 bulk 请求体：每行一个操作元数据或文档，以换行符分隔，末尾加换行
            lines = []
            for v in batch:
                lines.append(json.dumps({"index": {"_index": self.index_name, "_id": v.id}}))
                lines.append(json.dumps(asdict(v)))
            body = "\n".join(lines) + "\n"

            url = f"http://localhost:9200/_bulk"
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.post(
                    url,
                    content=body,
                    headers={"Content-Type": "application/x-ndjson"}
                )
                if resp.status_code != 200:
                    raise Exception(f"Bulk 写入失败: {resp.status_code} {resp.text}")
        logger.info(f"成功写入 {len(value_infos)} 条字段取值到 ES")