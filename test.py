import asyncio
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository

TEST_CASES = [
    {"query": "销售额", "expected": "order_amount"},
    {"query": "订单金额", "expected": "order_amount"},
    {"query": "用户ID", "expected": "customer_id"},
    {"query": "下单时间", "expected": "date_id"},  # 根据实际表名修改，如果是 created_at 就写 created_at
]

async def main():
    embedding_client_manager.init()
    qdrant_client_manager.init()

    repo = ColumnQdrantRepository(qdrant_client_manager.client)

    hit_count = 0

    for case in TEST_CASES:
        query = case["query"]
        expected = case["expected"]
        print(f"\n🔍 Query: {query}")

        # 使用新的异步封装
        embedding = await embedding_client_manager.aembed_query(query)
        results = await repo.search(embedding, limit=5, score_threshold=0.6)

        found = False
        for i, col in enumerate(results, 1):
            print(f"{i}. name={col.name} table={col.table_id}")
            if col.name == expected:
                found = True

        if found:
            print(f"✅ 命中期望字段: {expected}")
            hit_count += 1
        else:
            print(f"❌ 未命中期望字段: {expected}")

    total = len(TEST_CASES)
    print(f"\n命中率: {hit_count}/{total} = {hit_count/total:.2f}")
    await qdrant_client_manager.close()

asyncio.run(main())
# # # import asyncio
# # # from app.clients.qdrant_client_manager import qdrant_client_manager
# # #
# # # async def show_all_columns():
# # #     qdrant_client_manager.init()
# # #     client = qdrant_client_manager.client
# # #
# # #     # 滚动获取所有点
# # #     points, next_offset = await client.scroll(
# # #         collection_name="column_info_collection",
# # #         limit=100,
# # #         with_payload=True,
# # #         with_vectors=False,
# # #     )
# # #
# # #     print(f"总点数: {len(points)}")
# # #     for pt in points:
# # #         payload = pt.payload
# # #         print(f"字段: {payload.get('name')} | 表: {payload.get('table_id')} | 别名: {payload.get('alias')}")
# # #
# # #     await qdrant_client_manager.close()
# # #
# # # asyncio.run(show_all_columns())
# import asyncio
# from app.clients.qdrant_client_manager import qdrant_client_manager
#
# async def clear_qdrant():
#     qdrant_client_manager.init()
#     client = qdrant_client_manager.client
#
#     collection_name = "column_info_collection"  # 你一直在用的集合名
#
#     # 检查集合是否存在，存在则删除
#     if await client.collection_exists(collection_name):
#         await client.delete_collection(collection_name)
#         print(f"集合 {collection_name} 已删除，所有向量数据清空。")
#     else:
#         print(f"集合 {collection_name} 不存在，无需清空。")
#
#     await qdrant_client_manager.close()
#
# asyncio.run(clear_qdrant())