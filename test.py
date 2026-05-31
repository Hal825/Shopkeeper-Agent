from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# 查看所有集合
print("所有集合:", [c.name for c in client.get_collections().collections])

# 查看字段集合统计
if client.collection_exists("column_info_collection"):
    cnt = client.count("column_info_collection")
    print(f"column_info_collection 点数: {cnt.count}")
    # 随机看几条 payload
    points, _ = client.scroll("column_info_collection", limit=3)
    for p in points:
        print("字段 payload 示例:", p.payload)
else:
    print("column_info_collection 不存在")

# 查看指标集合统计
if client.collection_exists("metric_info_collection"):
    cnt = client.count("metric_info_collection")
    print(f"metric_info_collection 点数: {cnt.count}")
    points, _ = client.scroll("metric_info_collection", limit=3)
    for p in points:
        print("指标 payload 示例:", p.payload)
else:
    print("metric_info_collection 不存在")