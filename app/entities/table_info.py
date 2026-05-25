"""
表元数据业务实体

这一层对应文档里“先把配置描述转换成业务实体”的部分，用于在 Service
和 Repository 之间传递统一的表语义信息，而不是直接暴露 ORM 模型
"""

from dataclasses import dataclass


@dataclass
class TableInfo:
    """系统内部统一使用的表元数据表达"""

    id: str  # ✅ 表唯一标识（直接用表名）
    name: str  # ✅ 表名
    role: str  # ✅ 表角色：dim（维度表）或 fact（事实表）
    description: str  # ✅ 表业务描述