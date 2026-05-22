shopkeeper-agent/
├── app/                  # 后端源码主目录
│   ├── agent/            # 问数智能体与 LangGraph 图流程，例如节点、状态、上下文、图编排
│   ├── api/              # 对外 HTTP 接口层，对应 FastAPI 路由、依赖注入和请求参数结构
│   ├── clients/          # 各类基础服务客户端，例如 MySQL、ES、Qdrant、Embedding 服务
│   ├── conf/             # 配置类与配置加载工具，把 YAML 配置转换成代码可直接使用的对象
│   ├── core/             # 通用基础能力，例如日志、生命周期管理、请求上下文等
│   ├── entities/         # 业务实体定义，承接比 ORM 更贴近业务含义的数据结构
│   ├── models/           # ORM 模型，主要对应 MySQL 中的表结构
│   ├── prompt/           # 提示词加载工具，负责读取和组织静态 Prompt 资源
│   ├── repositories/     # 数据访问层，封装 MySQL / Qdrant / ES 的具体读写逻辑
│   ├── scripts/          # 工具脚本，例如构建元数据知识库、初始化或同步数据
│   └── services/         # 业务逻辑层，负责把客户端、仓储层和智能体能力真正串起来
├── conf/                 # 项目级 YAML 配置文件，例如数据库、向量库、ES、LLM、日志等配置
├── docker/               # 本地开发环境相关文件，例如 docker-compose 和自定义镜像资源
│   ├── elasticsearch/    # Elasticsearch 相关文件，例如 Dockerfile、插件或初始化资源
│   ├── embedding/        # Embedding 服务相关文件，例如模型目录或推理服务配置
│   └── mysql/            # MySQL 初始化 SQL、建表脚本或测试数据导入文件
├── logs/                 # 本地运行时日志输出目录
└── prompts/              # 静态提示词文件，和 app/prompt 中的加载工具配合使用