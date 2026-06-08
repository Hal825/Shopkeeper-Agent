import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.conf.app_config import app_config

async def test():
    # 创建数据库连接
    url = f"mysql+asyncmy://{app_config.db_dw.user}:{app_config.db_dw.password}@{app_config.db_dw.host}:{app_config.db_dw.port}/{app_config.db_dw.database}?charset=utf8mb4"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        session_factory = async_sessionmaker(conn)
        async with session_factory() as session:
            repo = DWMySQLRepository(session)

            # 测试正常 SQL
            try:
                result = await repo.run("SELECT 1", max_rows=10)
                print("✅ 正常 SQL 通过")
            except Exception as e:
                print(f"❌ 正常 SQL 被拦截: {e}")

            # 测试危险 SQL
            try:
                await repo.run("DROP TABLE fact_order")
                print("❌ DROP 应该被拦截")
            except ValueError as e:
                print(f"✅ DROP 被拦截: {e}")

            # 测试危险函数
            try:
                await repo.run("SELECT SLEEP(5)")
                print("❌ SLEEP 应该被拦截")
            except ValueError as e:
                print(f"✅ SLEEP 被拦截: {e}")

            # 测试 LIMIT 自动替换
            sql = "SELECT * FROM fact_order LIMIT 10000"
            new_sql = repo._add_limit(sql, 500)
            print(f"原始 SQL: {sql}")
            print(f"转换后: {new_sql}")

    await engine.dispose()

asyncio.run(test())