
"""
数仓 MySQL 仓储

这一层对应文档里的 DW Repository，职责是到真实数仓中补齐配置文件里
没有显式维护的信息，例如字段类型和字段示例值。Service 层只关心
“需要哪些信息”，具体怎样查数仓由仓储层统一封装

以及后续 SQL 校验和执行等逻辑，会在后续继续补进来
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DWMySQLRepository:
    """负责查询数仓真实表结构和字段样例值"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name: str) -> dict[str, str]:
        """查询整张表的字段类型，作为 ColumnInfo.type 的真实来源"""
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        result_dict = result.mappings().fetchall()
        return {row["Field"]: row["Type"] for row in result_dict}

    async def get_column_values(self, table_name: str, column_name: str, limit: int = 10) -> list:
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        # print(f"[DEBUG] 数据库连接: {self.session.bind.url}")
        # print(f"[DEBUG] 执行SQL: {sql}")

        result = await self.session.execute(text(sql))
        rows = result.fetchall()
        raw_values = [row[0] for row in rows]
        # print(f"[DEBUG] 原始返回值: {raw_values[:5]}... (总数 {len(raw_values)})")

        # 特别注意检查是否有 None 或空字符串
        non_null = [v for v in raw_values if v is not None and v != '']
        # print(f"[DEBUG] 非空值数量: {len(non_null)}")
        return raw_values

    async def get_db_info(self):
        """读取当前数仓数据库的方言和版本，供 SQL 生成提示词使用"""

        sql = "select version()"
        result = await self.session.execute(text(sql))
        version = result.scalar()

        # dialect 来自 SQLAlchemy 当前绑定的数据库方言，例如 mysql
        dialect = self.session.bind.dialect.name
        return {"dialect": dialect, "version": version}

    async def validate(self, sql: str):
        """用 EXPLAIN 让数据库提前解析 SQL，发现语法 表名 字段名等错误"""
        sql = f"explain {sql}"
        await self.session.execute(text(sql))

    async def run(self, sql: str) -> list[dict]:
        """执行最终 SQL，并把 SQLAlchemy 行对象转换成前端更易消费的字典列表"""
        # 这里做了两件事。第一，执行SQL：第二，把查询结果转成字典列表：
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]