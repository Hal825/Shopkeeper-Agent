"""
表过滤节点

负责从召回字段对应的表中筛选出真正需要参与 SQL 生成的表
这一步可以减少模型面对的表结构数量，降低生成错误 SQL 的概率
"""

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """根据用户问题裁剪候选表结构上下文"""
    # 获取写入器
    writer = runtime.stream_writer
    writer("过滤表信息")

    query = state["query"]
    table_infos: list[TableInfoState] = state["table_infos"]

    # table_infos 是嵌套结构，转成 YAML 后更适合放进提示词，也保留中文字段说明
    prompt = PromptTemplate(
        template=load_prompt("filter_table_info"),
        input_variables=["query", "table_infos"],
    )
    # filter_table_info prompt 要求模型只输出 JSON 对象：表名 -> 字段名列表
    output_parser = JsonOutputParser()
    # LCEL 管道：填充提示词 -> 调用模型 -> 解析 JSON
    chain = prompt | llm | output_parser
    # ainvoke是异步执行方法（async 版本）：
    result = await chain.ainvoke(
        {
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
        }
    )
    # 模型只负责选择，程序根据选择结果从原始 TableInfoState 中裁剪，避免模型重写复杂结构出错
    # result是LLM根据用户问题自动判断的“必需品清单”。
    # 代码遍历原字段列表，只把清单上有的字段保留下来。
    filtered_table_infos: list[TableInfoState] = []
    for table_info in table_infos:
        # 表名在 LLM 选择中？
        if table_info["name"] in result:
            # 裁剪字段列表
            table_info["columns"] = [
                column_info
                for column_info in table_info["columns"]
                if column_info["name"] in result[table_info["name"]]
            ]
            filtered_table_infos.append(table_info)

    logger.info(
        f"过滤后的表信息：{[filtered_table_info['name'] for filtered_table_info in filtered_table_infos]}"
    )
    return {"table_infos": filtered_table_infos}