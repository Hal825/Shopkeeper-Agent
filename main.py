"""
FastAPI 应用入口

负责创建后端应用实例，并把各业务模块中的 router 挂载到同一个 app 上。
本章先只注册问数查询接口，后续 lifespan、middleware、Depends 等工程能力
也会从这里逐步接入。
"""

from fastapi import FastAPI
from app.api.lifespan import lifespan  # 确保导入了 lifespan
from app.api.routers.query_router import query_router

app = FastAPI(lifespan=lifespan)  # 必须传递 lifespan

# 把查询路由注册进应用；没有挂载时，/docs 和真实 HTTP 请求都访问不到该接口,让app知道有这个东西的存在
app.include_router(query_router)