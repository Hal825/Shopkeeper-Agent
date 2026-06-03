import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ==================== 数据库配置（请根据实际情况修改） ====================
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "lzs"
DB_PASSWORD = "Lzs666"
DB_NAME = "meta"

# 输出文件路径（可自行修改）
OUTPUT_COLUMN_NDJSON = "column_info.ndjson"
OUTPUT_METRIC_NDJSON = "metric_info.ndjson"


def get_engine():
    """创建 SQLAlchemy 数据库引擎"""
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    return create_engine(url, echo=False)


def export_columns(session, output_file):
    """导出 column_info 表到 NDJSON 文件"""
    # 查询所有字段（不包含 examples 过大的内容，但 examples 已经是 JSON 字符串）
    sql = text("""
        SELECT id, name, type, role, examples, description, alias, table_id
        FROM column_info
    """)
    rows = session.execute(sql).fetchall()
    print(f"找到 {len(rows)} 条字段记录")

    with open(output_file, "w", encoding="utf-8") as f:
        for row in rows:
            # 解析 JSON 字段（examples 和 alias）
            examples = row.examples
            if examples and isinstance(examples, str):
                try:
                    examples = json.loads(examples)
                except:
                    examples = []
            alias = row.alias
            if alias and isinstance(alias, str):
                try:
                    alias = json.loads(alias)
                except:
                    alias = []

            record = {
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "role": row.role,
                "examples": examples if examples else [],
                "description": row.description,
                "alias": alias if alias else [],
                "table_id": row.table_id,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"字段数据已导出到 {output_file}")


def export_metrics(session, output_file):
    """导出 metric_info 表到 NDJSON 文件"""
    sql = text("""
        SELECT id, name, description, relevant_columns, alias
        FROM metric_info
    """)
    rows = session.execute(sql).fetchall()
    print(f"找到 {len(rows)} 条指标记录")

    with open(output_file, "w", encoding="utf-8") as f:
        for row in rows:
            # 解析 JSON 字段
            relevant_columns = row.relevant_columns
            if relevant_columns and isinstance(relevant_columns, str):
                try:
                    relevant_columns = json.loads(relevant_columns)
                except:
                    relevant_columns = []
            alias = row.alias
            if alias and isinstance(alias, str):
                try:
                    alias = json.loads(alias)
                except:
                    alias = []

            record = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "relevant_columns": relevant_columns,
                "alias": alias,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"指标数据已导出到 {output_file}")


def main():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        export_columns(session, OUTPUT_COLUMN_NDJSON)
        export_metrics(session, OUTPUT_METRIC_NDJSON)
    finally:
        session.close()

    print("导出完成！")


if __name__ == "__main__":
    main()