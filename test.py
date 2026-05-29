# import asyncio
# from app.clients.embedding_client_manager import embedding_client_manager
# from app.clients.qdrant_client_manager import qdrant_client_manager
# from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
#
# TEST_CASES = [
#     {"query": "销售额", "expected": "order_amount"},
#     {"query": "订单金额", "expected": "order_amount"},
#     {"query": "用户ID", "expected": "customer_id"},
#     {"query": "下单时间", "expected": "date_id"},  # 根据实际表名修改，如果是 created_at 就写 created_at
# ]
#
# async def main():
#     embedding_client_manager.init()
#     qdrant_client_manager.init()
#
#     repo = ColumnQdrantRepository(qdrant_client_manager.client)
#
#     hit_count = 0
#
#     for case in TEST_CASES:
#         query = case["query"]
#         expected = case["expected"]
#         print(f"\n🔍 Query: {query}")
#
#         # 使用新的异步封装
#         embedding = await embedding_client_manager.aembed_query(query)
#         results = await repo.search(embedding, limit=5, score_threshold=0.6)
#
#         found = False
#         for i, col in enumerate(results, 1):
#             print(f"{i}. name={col.name} table={col.table_id}")
#             if col.name == expected:
#                 found = True
#
#         if found:
#             print(f"✅ 命中期望字段: {expected}")
#             hit_count += 1
#         else:
#             print(f"❌ 未命中期望字段: {expected}")
#
#     total = len(TEST_CASES)
#     print(f"\n命中率: {hit_count}/{total} = {hit_count/total:.2f}")
#     await qdrant_client_manager.close()
#
# asyncio.run(main())
from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200")
resp = es.count(index="value_info")
print(resp['count'])