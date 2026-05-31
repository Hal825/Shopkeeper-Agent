"""
电商问数 Agent 使用的大模型实例

集中初始化一个 OpenAI 兼容的 Chat Model，供节点或本地测试直接复用
"""
from app.conf.app_config import app_config

# 统一从配置读取模型三件套，节点只复用 llm，不重复初始化模型连接
import os

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

# 1. 定义 DeepSeek 模型（关键：必须填 base_url 和 api_key）
llm = init_chat_model(
    model="deepseek-v4-pro",
    base_url="https://api.deepseek.com/v1",  # DeepSeek 官方接口地址
    api_key=os.getenv("DEEPSEEK_API_KEY"),       # 你必须填自己的密钥
    model_provider="deepseek",          # 提供商
    temperature=0.7,                         # 可选参数
)
if __name__ == "__main__":
    # 本地快速验证 LLM 配置是否能正常调用
    print(llm.invoke("你好").content)