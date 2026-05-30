#!/usr/bin/env python3
"""
从 Docker 容器内的 MySQL 导出数据为 NDJSON 文件
使用 docker exec 调用 mysql 客户端，避免网络连接问题
"""

import subprocess
import json
import sys
from pathlib import Path

# ========== 配置区 ==========
CONTAINER_NAME = "mysql"  # MySQL 容器名称
MYSQL_USER = "lzs"
MYSQL_PASSWORD = "Lzs666"
DATABASE = "meta"

# 导出文件路径（绝对路径，需确保有写入权限）
OUTPUT_DIR = Path(r"D:\Code\PC-Project\SA\shopkeeper-agent\app\scripts")
COLUMN_NDJSON = OUTPUT_DIR / "column_info.ndjson"
METRIC_NDJSON = OUTPUT_DIR / "metric_info.ndjson"

# 要导出的表与字段映射
TABLES = {
    "column_info": {
        "columns": [
            "id", "name", "type", "role", "description", "alias", "table_id"
        ],
        "output_file": COLUMN_NDJSON
    },
    "metric_info": {
        "columns": [
            "id", "name", "description", "relevant_columns", "alias"
        ],
        "output_file": METRIC_NDJSON
    }
}


# ============================

def run_docker_mysql_query(sql: str) -> str:
    """在容器中执行 MySQL 查询，返回原始输出（文本）"""
    cmd = [
        "docker", "exec", CONTAINER_NAME,
        "mysql",
        f"-u{MYSQL_USER}",
        f"-p{MYSQL_PASSWORD}",
        "-D", DATABASE,
        "-N",  # 不输出列名
        "-e", sql
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True,
            timeout=60
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"MySQL 查询执行失败，错误码: {e.returncode}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("查询超时")
        sys.exit(1)


def export_table(table_name: str, columns: list, output_file: Path):
    """导出单个表为 NDJSON 文件"""
    # 构造 JSON_OBJECT 字符串
    json_parts = []
    for col in columns:
        # 使用单引号包裹键名，值直接写列名
        json_parts.append(f"'{col}', {col}")
    json_obj = f"JSON_OBJECT({', '.join(json_parts)})"
    sql = f"SELECT {json_obj} FROM {table_name};"

    print(f"正在导出表 {table_name} ...")
    raw_output = run_docker_mysql_query(sql)

    # 写入文件（每行一个 JSON）
    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = raw_output.strip().split('\n')
    # 过滤掉可能的空行
    lines = [ln for ln in lines if ln.strip()]

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in lines:
            # 验证是否为合法 JSON（可选）
            try:
                json.loads(line)
            except json.JSONDecodeError:
                print(f"警告: 无效的 JSON 行，跳过：{line[:100]}")
                continue
            f.write(line + '\n')

    print(f"已导出 {len(lines)} 条记录到 {output_file}")


def main():
    print("开始从 Docker MySQL 容器导出数据...")
    print(f"输出目录: {OUTPUT_DIR}")

    for table_name, info in TABLES.items():
        export_table(table_name, info["columns"], info["output_file"])

    print("导出完成！")
    print(f"文件位置: {COLUMN_NDJSON}, {METRIC_NDJSON}")


if __name__ == "__main__":
    main()