import asyncio
from pydoc import text

from app.clients.mysql_client_manager import meta_mysql_client_manager

meta_mysql_client_manager.init()
print("session_factory =", meta_mysql_client_manager.session_factory)

async def test():
    async with meta_mysql_client_manager.session_factory() as session:
        result = await session.execute(text("SELECT 1"))
        print(result.scalar())

asyncio.run(test())