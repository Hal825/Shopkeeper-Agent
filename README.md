```text
📦 shopkeeper-agent/
│
├── 📂 app/                        # 🧠 后端源码主目录
│   ├── 📂 agent/                  # 问数智能体 & LangGraph 图流程
│   │                              #   ├─ 节点 (nodes)
│   │                              #   ├─ 状态 (state)
│   │                              #   ├─ 上下文 (context)
│   │                              #   └─ 图编排 (graph)
│   ├── 📂 api/                    # 🌐 对外 HTTP 接口层
│   │                              #   FastAPI 路由 · 依赖注入 · 请求参数结构
│   ├── 📂 clients/                # 🔌 基础服务客户端
│   │                              #   MySQL · Elasticsearch · Qdrant · Embedding 服务
│   ├── 📂 conf/                   # ⚙️ 配置类 & 加载工具
│   │                              #   将 YAML 配置转为代码可用的对象
│   ├── 📂 core/                   # 🏗️ 通用基础能力
│   │                              #   日志 · 生命周期管理 · 请求上下文
│   ├── 📂 entities/               # 📋 业务实体定义
│   │                              #   比 ORM 模型更贴近业务含义的数据结构
│   ├── 📂 models/                 # 🗃️ ORM 模型
│   │                              #   对应 MySQL 表结构
│   ├── 📂 prompt/                 # 💬 提示词加载工具
│   │                              #   读取 & 组织静态 Prompt 资源
│   ├── 📂 repositories/           # 📡 数据访问层
│   │                              #   封装 MySQL · Qdrant · Elasticsearch 的读写逻辑
│   ├── 📂 scripts/                # 🔧 工具脚本
│   │                              #   构建元数据知识库 · 初始化/同步数据
│   └── 📂 services/               # 🧩 业务逻辑层
│                                  #   串联 clients · repositories · agent
│
├── 📂 conf/                       # ⚙️ 项目级 YAML 配置
│                                  #   数据库 · 向量库 · ES · LLM · 日志
│
├── 📂 docker/                     # 🐳 本地开发环境
│   ├── 📂 elasticsearch/          # Elasticsearch 相关
│   │                              #   Dockerfile · 插件 · 初始化资源
│   ├── 📂 embedding/              # 🤖 Embedding 服务
│   │                              #   模型目录 · 推理服务配置
│   └── 📂 mysql/                  # 🗄️ MySQL 初始化
│                                  #   SQL 脚本 · 建表 · 测试数据
│
├── 📂 logs/                       # 📝 本地运行时日志
│
└── 📂 prompts/                    # 📄 静态提示词文件
                                   #   与 app/prompt 加载工具配合使用
```
