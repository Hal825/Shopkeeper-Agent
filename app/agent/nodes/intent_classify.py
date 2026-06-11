import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def intent_classify(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "理解用户意图", "status": "running"})

    try:
        query = state["query"]
        messages = state.get("messages", [])
        last_assistant_msgs = []
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                last_assistant_msgs.append(msg.get("content", ""))
                if len(last_assistant_msgs) > 5:
                    break
        last_assistant_msg = "\n".join(last_assistant_msgs)  # 如果列表为空，得到空字符串

        prompt = PromptTemplate(
            template=load_prompt("intent_classify"),
            input_variables=["query", "last_assistant_msg"],
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({
            "query": query,
            "last_assistant_msg": last_assistant_msg,
        })

        intent = result.get("intent", "data_query")
        reply = result.get("reply", "")
        # 为闲聊意图提供默认回复，避免空字符串
        if intent == "chitchat" and not reply:
            reply = "我是电商问数助手，专注于数据查询和分析。您可以问我类似“统计华北地区的销售总额”的问题。"

        logger.info(f"意图分类结果：{intent}")
        writer({"type": "progress", "step": "理解用户意图", "status": "success"})
        return {"intent": intent, "intent_reply": reply}
    except Exception as e:
        logger.error(f"意图分类节点失败: {e}")
        writer({"type": "progress", "step": "理解用户意图", "status": "error"})
        # 降级：默认为数据查询意图，继续流程
        return {"intent": "data_query", "intent_reply": ""}