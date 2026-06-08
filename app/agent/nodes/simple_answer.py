from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def recap_answer(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "回顾上次回答", "status": "running"})

    try:
        messages = state.get("messages", [])
        last_assistant_content = ""
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                last_assistant_content = msg.get("content", "")
                break

        if last_assistant_content:
            reply = f"您上一次问的是：{last_assistant_content}"
        else:
            reply = "您还没有与我进行过对话，请提出一个数据查询问题。"

        writer({"type": "explanation", "text": reply})
        writer({"type": "progress", "step": "回顾上次回答", "status": "success"})
        # 关键：清空 steps，避免前端显示旧的流程图
        return {"steps": []}
    except Exception as e:
        logger.error(f"回顾回答节点失败: {e}")
        writer({"type": "progress", "step": "回顾上次回答", "status": "error"})
        writer({"type": "error", "message": "无法回顾上次回答，请重试。"})
        return {"steps": []}

async def chitchat_answer(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "闲聊回复", "status": "running"})

    try:
        reply = state.get("intent_reply", "我是电商问数助手，专注于数据查询和分析。您可以问我类似“统计华北地区的销售总额”的问题。")
        writer({"type": "explanation", "text": reply})
        writer({"type": "progress", "step": "闲聊回复", "status": "success"})
        return {}
    except Exception as e:
        logger.error(f"闲聊回复节点失败: {e}")
        writer({"type": "progress", "step": "闲聊回复", "status": "error"})
        writer({"type": "error", "message": "回复失败，请稍后重试。"})
        return {}


async def help_answer(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "帮助说明", "status": "running"})

    try:
        help_text = """📘 **使用说明**
                    我可以帮您查询和分析数据，支持以下问题类型：
                    - 统计销售额、订单量、GMV等
                    - 按地区、时间、品类等维度筛选
                    - 排序、分组、聚合
                    
                    示例问题：
                    - “统计华北地区的销售总额”
                    - “查询2025年第一季度各大区的GMV，按从高到低排序”
                    - “华东地区销量最高的前5个商品”
                    
                    请用自然语言向我提问。"""
        writer({"type": "explanation", "text": help_text})
        writer({"type": "progress", "step": "帮助说明", "status": "success"})
        return {}
    except Exception as e:
        logger.error(f"帮助说明节点失败: {e}")
        writer({"type": "progress", "step": "帮助说明", "status": "error"})
        writer({"type": "error", "message": "无法获取帮助信息，请稍后重试。"})
        return {}