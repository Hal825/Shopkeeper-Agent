import asyncio
import os
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings  # 只用本地模型
from app.conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self, config: EmbeddingConfig):
        self.client: Optional[HuggingFaceEmbeddings] = None
        self.config = config

    def init(self):
        # 自动计算项目根目录，避免相对路径问题
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(project_root, "docker", "embedding", "bge-small-zh")

        self.client = HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

    # 提供异步友好的封装
    async def aembed_query(self, text: str):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.client.embed_query, text)

    async def aembed_documents(self, texts: list[str]):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.client.embed_documents, texts)


# 单例
embedding_client_manager = EmbeddingClientManager(app_config.embedding)


if __name__ == "__main__":
    embedding_client_manager.init()
    async def test():
        vec = await embedding_client_manager.aembed_query("测试")
        print(len(vec))
    asyncio.run(test())