"""
字段元数据业务实体

字段配置中的业务语义、从数仓补齐的真实类型，以及抽样得到的示例值，
都会汇总到这个对象里，再继续流向元数据库与后续检索链路
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ColumnInfo:
    """系统内部统一使用的字段元数据表达"""

    id: str  # ✅ 唯一标识：表名.字段名
    name: str  # ✅ 字段名
    type: str  # ✅ 字段类型（从DW查）
    role: str  # ✅ 字段角色：primary_key/foreign_key/dimension/measure
    examples: list[Any]  # ✅ 示例值（从DW查）
    description: str  # ✅ 业务描述
    alias: list[str]  # ✅ 别名列表
    table_id: str  # ✅ 所属表名

# 常见的 type 值
# type 值	含义	示例数据
# int	整数	1, 100, 999
# bigint	大整数	1000000000
# varchar(50)	变长字符串，最长50个字符	"华东", "张三"
# decimal(10,2)	小数，总共10位，小数点后2位	99.90, 1000.00
# date	日期	2024-01-01
# datetime	日期时间	2024-01-01 10:30:00
# boolean	布尔值	true, false

# 常见的 role 值
# role	含义	示例字段	业务用途
# primary_key	主键	region_id, order_id	唯一标识一行数据
# foreign_key	外键	customer_id, product_id	关联其他表
# dimension	维度	region_name, category	描述性字段，用于分组/筛选
# measure	度量	order_amount, quantity	可计算的数值，用于聚合