import json
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from langchain_huggingface import HuggingFaceEmbeddings

# 配置
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
EMBEDDING_MODEL = "D:/Code/PC-Project/SA/shopkeeper-agent/docker/embedding/bge-small-zh"
VECTOR_SIZE = 512
COLLECTION_COLUMN = "column_info_collection"
COLLECTION_METRIC = "metric_info_collection"

COLUMN_NDJSON = "column_info.ndjson"
METRIC_NDJSON = "metric_info.ndjson"


def load_ndjson(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    print(f"从 {file_path} 加载 {len(data)} 条记录")
    return data


def get_text_for_embedding(item):
    name = item.get("name", "")
    description = item.get("description", "")
    alias = item.get("alias", [])
    if isinstance(alias, str):
        try:
            alias = json.loads(alias)
        except:
            alias = []
    if not isinstance(alias, list):
        alias = []
    alias_str = " ".join(alias)
    text = f"{name} {description} {alias_str}".strip()
    return text


def recreate_collection(client, collection_name, vector_size):
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        print(f"删除已存在的 collection: {collection_name}")
        client.delete_collection(collection_name)
    print(f"创建 collection: {collection_name} (size={vector_size})")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def main():
    print("开始从 NDJSON 文件导入元数据到 Qdrant...")

    # 加载 Embedding 模型
    print(f"加载 Embedding 模型: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # 连接 Qdrant
    print(f"连接 Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    qdrant_client = QdrantClient(
        url=f"http://{QDRANT_HOST}:{QDRANT_PORT}",
        timeout=120.0,
        prefer_grpc=False
    )

    # 重建 collections
    recreate_collection(qdrant_client, COLLECTION_COLUMN, VECTOR_SIZE)
    recreate_collection(qdrant_client, COLLECTION_METRIC, VECTOR_SIZE)

    # 导入字段（使用自增整数作为点ID）
    columns = load_ndjson(COLUMN_NDJSON)
    points = []
    for idx, col in enumerate(columns, start=1):
        text = get_text_for_embedding(col)
        if not text:
            print(f"警告: 字段 {col.get('id')} 没有有效文本，跳过")
            continue
        vector = embeddings.embed_query(text)
        # 点ID使用整数（序号），原始ID存入payload的 original_id 字段
        point = PointStruct(
            id=idx,  # 整数ID
            vector=vector,
            payload={
                "original_id": col["id"],  # 保存原始字符串ID
                "name": col["name"],
                "type": col.get("type"),
                "role": col.get("role"),
                "description": col.get("description"),
                "alias": col.get("alias"),
                "table_id": col.get("table_id"),
            }
        )
        points.append(point)
    if points:
        print(f"正在向 {COLLECTION_COLUMN} 插入 {len(points)} 条向量...")
        qdrant_client.upsert(collection_name=COLLECTION_COLUMN, points=points)
        print("字段导入完成")
    else:
        print("没有字段需要导入")

    # 导入指标（同样处理）
    metrics = load_ndjson(METRIC_NDJSON)
    points = []
    for idx, metric in enumerate(metrics, start=1):
        text = get_text_for_embedding(metric)
        if not text:
            print(f"警告: 指标 {metric.get('id')} 没有有效文本，跳过")
            continue
        vector = embeddings.embed_query(text)
        rel_cols = metric.get("relevant_columns", [])
        if isinstance(rel_cols, str):
            try:
                rel_cols = json.loads(rel_cols)
            except:
                rel_cols = []
        point = PointStruct(
            id=idx,  # 整数ID
            vector=vector,
            payload={
                "original_id": metric["id"],
                "name": metric["name"],
                "description": metric.get("description"),
                "relevant_columns": rel_cols,
                "alias": metric.get("alias"),
            }
        )
        points.append(point)
    if points:
        print(f"正在向 {COLLECTION_METRIC} 插入 {len(points)} 条向量...")
        qdrant_client.upsert(collection_name=COLLECTION_METRIC, points=points)
        print("指标导入完成")
    else:
        print("没有指标需要导入")

    print("所有数据导入完成！")


if __name__ == "__main__":
    main()