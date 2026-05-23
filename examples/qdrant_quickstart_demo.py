import asyncio

from qdrant_client import AsyncQdrantClient, models  # 修正1：models 不是 client_model

QDRANT_URL = "http://localhost:6333"  #代码定义了Qdrant 服务器的连接地址
COLLECTION_NAME = "quickstart_demo"
VECTOR_SIZE = 4 #定义了向量的维度，即每个向量由多少个浮点数组成


async def recreate_collection(client):
    # 修正2：扁平风格调用，不是 client.collection.xxx
    if await client.collection_exists(COLLECTION_NAME):
        await client.delete_collection(COLLECTION_NAME) #表和数据一起删，测试的时候用

    # 修正3：使用 models.VectorParams，拼写 Distance
    await client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(  # 注意是 vectors_config，在创建 Qdrant 集合时，配置向量的存储规则。
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,  # Distance 拼写正确
        ),
    )
    print(f"1. 已创建集合：{COLLECTION_NAME}")

async def add_vector(client):
    await client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id = 1,
                vector=[0.05, 0.61, 0.76, 0.74],
                payload={"name": "订单分析", "type": "report"},
            ),
            models.PointStruct(
                id=2,
                vector=[0.19, 0.81, 0.75, 0.11],
                payload={"name": "销量趋势", "type": "metric"},
            ),
            models.PointStruct(
                id=3,
                vector=[0.36, 0.55, 0.47, 0.94],
                payload={"name": "区域销售额", "type": "dimension"},
            ),
        ]
    )
    print("2. 已写入 3 个向量点。")

async def run_query(client):
    query_vector = [0.2, 0.1, 0.9, 0.7] #用于搜索的查询向量，代表用户想要查找的"目标"。
    result = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3,
        with_payload=True,
    )
    print(f"3. 查询向量：{query_vector}")
    print("4. 查询结果：")

    # result 的类型是 QueryPointsResult
    # result.points  # 这是一个列表，里面装着查询结果，类似这样：
    # [
    #   ScoredPoint(id=1, score=0.8946, payload={'name': '订单分析'}),
    #   ScoredPoint(id=3, score=0.8387, payload={'name': '区域销售额'}),
    #   ScoredPoint(id=2, score=0.6660, payload={'name': '销量趋势'})
    # ]
    # enumerate 是 Python 内置函数，用于同时获取索引和值，
    # points = ["苹果", "香蕉", "橘子"] enumerate 把列表变成这样：
    # # [(0, "苹果"), (1, "香蕉"), (2, "橘子")]，start=1 让索引从 1 开始计数，而不是默认的 0
    for i, point in enumerate(result.points, start=1):
        print(
            f"   {i}) id={point.id}, score={point.score:.4f}, payload={point.payload}"
        )

async def main():
    client = AsyncQdrantClient(url = QDRANT_URL)

    try:
        await recreate_collection(client)
        await add_vector(client)
        await run_query(client)
    finally:
        await client.delete_collection(COLLECTION_NAME)
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())