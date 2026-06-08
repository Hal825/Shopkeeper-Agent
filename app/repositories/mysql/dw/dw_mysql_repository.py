"""
数仓 MySQL 仓储

职责：
- 到真实数仓中补齐字段类型和示例值（原有功能）
- 执行最终 SQL 并返回字典列表（原有功能）
- 增加安全控制：只读检查、危险关键字过滤、查询超时、结果行数限制
"""
import re

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

    # ==================== 2. 安全增强的校验和执行方法 ====================

    # ---------- 静态正则表达式（类级别） ----------
    _SELECT_PATTERN = re.compile(r'^\s*(?:SELECT\b)', re.IGNORECASE)
    _FORBIDDEN_KEYWORDS_PATTERN = re.compile(
        r'\b(?:INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|REPLACE)\b',
        re.IGNORECASE
    )
    _DANGEROUS_PATTERNS = [
        re.compile(r'INTO\s+OUTFILE', re.IGNORECASE),
        re.compile(r'INTO\s+DUMPFILE', re.IGNORECASE),
        re.compile(r'LOAD_FILE\s*\(', re.IGNORECASE),
        re.compile(r'SLEEP\s*\(', re.IGNORECASE),
        re.compile(r'BENCHMARK\s*\(', re.IGNORECASE),
        re.compile(r'UNION\s+SELECT', re.IGNORECASE),
        re.compile(r'CONCAT\s*\(.*0x[0-9a-f]', re.IGNORECASE),
        re.compile(r'BINLOG\s', re.IGNORECASE),
        re.compile(r'SUBSTR\s*\(', re.IGNORECASE),
    ]
    _LIMIT_PATTERN = re.compile(r'\bLIMIT\s+(\d+)(?:\s*,\s*(\d+))?', re.IGNORECASE)

    @staticmethod
    def _is_readonly(sql: str) -> bool:
        """检查 SQL 是否为只读查询（去除注释后必须以 SELECT 开头，且不含禁止关键字）"""
        # 去除单行注释 -- 和 #
        sql_no_comment = re.sub(r'--[^\n]*|\#.*', '', sql)
        # 去除多行注释 /* ... */
        sql_no_comment = re.sub(r'/\*.*?\*/', '', sql_no_comment, flags=re.DOTALL)
        sql_clean = sql_no_comment.strip()
        if not sql_clean:
            return False
        if not DWMySQLRepository._SELECT_PATTERN.match(sql_clean):
            return False
        if DWMySQLRepository._FORBIDDEN_KEYWORDS_PATTERN.search(sql_clean):
            return False
        return True

    @staticmethod
    def _contains_dangerous_pattern(sql: str) -> bool:
        """检查 SQL 是否包含危险函数或注入模式"""
        for pattern in DWMySQLRepository._DANGEROUS_PATTERNS:
            if pattern.search(sql):
                return True
        return False

    @staticmethod
    def _add_limit(sql: str, default_limit: int) -> str:
        """自动添加或限制 LIMIT 子句"""
        sql_clean = sql.rstrip(';')
        match = DWMySQLRepository._LIMIT_PATTERN.search(sql_clean)
        if not match:
            return f"{sql_clean} LIMIT {default_limit}"
        groups = match.groups()
        if groups[1] is not None:  # LIMIT offset, count
            offset = int(groups[0])
            existing_limit = int(groups[1])
        else:  # LIMIT count
            offset = 0
            existing_limit = int(groups[0])
        new_limit = min(existing_limit, default_limit)
        if new_limit == existing_limit:
            return sql
        if groups[1] is not None:
            new_clause = f"LIMIT {offset}, {new_limit}"
        else:
            new_clause = f"LIMIT {new_limit}"
        return re.sub(DWMySQLRepository._LIMIT_PATTERN, new_clause, sql_clean)

    # ---------- 安全校验 ----------
    async def validate(self, sql: str):
        """
        校验 SQL 语法（EXPLAIN）并执行安全检查
        用于 validate_sql 节点
        """
        if not self._is_readonly(sql):
            raise ValueError("只允许 SELECT 查询")
        if self._contains_dangerous_pattern(sql):
            raise ValueError("SQL 包含危险关键字")
        await self.session.execute(text(f"EXPLAIN {sql}"))

    # ---------- 安全执行 ----------
    async def run(self, sql: str, timeout_ms: int = 30000, max_rows: int = 1000) -> list[dict]:
        """
        执行最终 SQL，带完整安全保护：
        - 只读检查
        - 危险关键字过滤
        - 查询超时控制
        - 自动限制返回行数
        """
        # 1. 安全检查
        if not self._is_readonly(sql):
            raise ValueError("只允许执行 SELECT 查询")
        if self._contains_dangerous_pattern(sql):
            raise ValueError("SQL 包含危险关键字")

        # 2. 设置查询超时
        await self.session.execute(text(f"SET SESSION max_execution_time = {timeout_ms}"))

        # 3. 自动处理 LIMIT
        sql_with_limit = self._add_limit(sql, max_rows)

        try:
            result = await self.session.execute(text(sql_with_limit))
            rows = [dict(row) for row in result.mappings().fetchall()]
            return rows[:max_rows]  # 二次截断，确保不超过限制
        finally:
            # 恢复超时设置（避免影响后续查询）
            await self.session.execute(text("SET SESSION max_execution_time = 0"))