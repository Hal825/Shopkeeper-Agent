import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, es_config: ESConfig):
        # 保存 ES 配置对象，后面初始化客户端时会从这里读取 host 和 port
        self.es_config = es_config
        # 先把 client 声明出来，真正初始化放到 init() 中进行
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        # 根据配置文件拼出 ES 服务地址
        return f"http://{self.es_config.host}:{self.es_config.port}"

    def init(self):
        # 创建异步 ES 客户端
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        # 在程序退出时统一关闭客户端连接
        if self.client:
            await self.client.close()

    async def ensure_index(self, index_name: str, mappings: dict, force_recreate: bool = False):
        """确保索引存在，可选择是否强制重建

        Args:
            index_name: 索引名称
            mappings: 索引映射定义
            force_recreate: 是否强制删除并重建索引
        """
        if not self.client:
            raise RuntimeError("ES客户端未初始化，请先调用 init()")

        # 检查索引是否存在
        exists = await self.client.indices.exists(index=index_name)

        if exists:
            if force_recreate:
                print(f"索引 '{index_name}' 已存在，正在删除...")
                await self.client.indices.delete(index=index_name)
                print(f"索引 '{index_name}' 已删除")
            else:
                print(f"索引 '{index_name}' 已存在，跳过创建")
                return

        # 创建索引
        await self.client.indices.create(
            index=index_name,
            mappings=mappings,
        )
        print(f"索引 '{index_name}' 创建成功")

    async def bulk_insert(self, index_name: str, documents: list):
        """批量插入文档

        Args:
            index_name: 索引名称
            documents: 文档列表，每个文档是一个字典
        """
        if not self.client:
            raise RuntimeError("ES客户端未初始化，请先调用 init()")

        # 构建 bulk 操作列表
        operations = []
        for doc in documents:
            operations.append({"index": {"_index": index_name}})
            operations.append(doc)

        # 执行批量插入
        result = await self.client.bulk(operations=operations)

        if result.get("errors"):
            print(f"批量插入出现错误: {result}")
        else:
            print(f"成功插入 {len(documents)} 条文档")

        return result

    async def search(self, index_name: str, query: dict, size: int = 10):
        """搜索文档

        Args:
            index_name: 索引名称
            query: 查询条件
            size: 返回结果数量
        """
        if not self.client:
            raise RuntimeError("ES客户端未初始化，请先调用 init()")

        resp = await self.client.search(
            index=index_name,
            query=query,
            size=size
        )
        return resp


# 创建一个全局可复用的 ES 客户端管理器对象
es_client_manager = ESClientManager(app_config.es)

if __name__ == "__main__":
    # 先初始化客户端
    es_client_manager.init()


    async def test():
        # 定义索引映射
        books_mappings = {
            "dynamic": False,
            "properties": {
                "name": {"type": "text"},
                "author": {"type": "text"},
                "release_date": {"type": "date", "format": "yyyy-MM-dd"},
                "page_count": {"type": "integer"},
            },
        }

        # 确保索引存在（如果已存在则跳过创建）
        await es_client_manager.ensure_index(
            index_name="my-books",
            mappings=books_mappings,
            force_recreate=False  # 改为 True 可以强制重建
        )

        # 准备要插入的数据
        books_data = [
            {
                "name": "Revelation Space",
                "author": "Alastair Reynolds",
                "release_date": "2000-03-15",
                "page_count": 585,
            },
            {
                "name": "1984",
                "author": "George Orwell",
                "release_date": "1985-06-01",
                "page_count": 328,
            },
            {
                "name": "Fahrenheit 451",
                "author": "Ray Bradbury",
                "release_date": "1953-10-15",
                "page_count": 227,
            },
            {
                "name": "Brave New World",
                "author": "Aldous Huxley",
                "release_date": "1932-06-01",
                "page_count": 268,
            },
            {
                "name": "The Handmaids Tale",
                "author": "Margaret Atwood",
                "release_date": "1985-06-01",
                "page_count": 311,
            },
        ]

        # 批量插入数据
        await es_client_manager.bulk_insert(
            index_name="my-books",
            documents=books_data
        )

        # 执行搜索
        resp = await es_client_manager.search(
            index_name="my-books",
            query={"match": {"name": "brave"}}
        )

        # 打印搜索结果
        print("\n搜索结果:")
        print(f"总共找到: {resp['hits']['total']['value']} 条结果")
        for hit in resp['hits']['hits']:
            print(f"- {hit['_source']['name']} by {hit['_source']['author']}")

        # 测试结束后关闭客户端连接
        await es_client_manager.close()


    # 运行异步测试函数
    asyncio.run(test())