from dataclasses import dataclass
from pathlib import Path
import os
import re

from omegaconf import OmegaConf


# ====== 所有 dataclass 定义保持不变 ======
@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str

@dataclass
class Console:
    enable: bool
    level: str

@dataclass
class LoggingConfig:
    file: File
    console: Console

@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int

@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str

@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str

@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str

@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig


# ====================== 配置加载（修改部分） ======================
config_file = Path(__file__).resolve().parent / "app_config.yaml"

# 先读取 YAML 文件原始内容
with open(config_file, "r", encoding="utf-8") as f:
    raw_yaml = f.read()

# 手动替换 ${VAR_NAME} 为环境变量的值
def replace_env_var(match):
    var_name = match.group(1)
    return os.environ.get(var_name, f"${{{var_name}}}")  # 没找到就保留原样

raw_yaml = re.sub(r'\$\{(\w+)\}', replace_env_var, raw_yaml)

# 再用 OmegaConf 加载替换后的内容
context = OmegaConf.create(raw_yaml)

# 生成 schema 并合并
schema = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema, context)) #内容+结构


# ====================== 测试 ======================
if __name__ == '__main__':
    print("ES 地址 =", app_config.es.host)
    print("LLM 模型 =", app_config.llm.model_name)
    print("配置加载成功！")