import asyncio

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository

async def main():
    embedding_client_manager.init()
    qdrant_client_manager.init()

    repo = ColumnQdrantRepository(qdrant_client_manager.client)
    embedding = await embedding_client_manager.client.aembed_query("销售额")
    results = await repo.search(embedding, limit=5)

    for i, item in enumerate(results, 1):
        print(f"{i}. id={item.id} name={item.name} desc={item.description} table={item.table_id}")

    await qdrant_client_manager.close()

asyncio.run(main())
