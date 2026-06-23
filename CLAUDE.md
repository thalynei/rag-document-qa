# CLAUDE.md — RAG Document QA 项目指南

## 项目概述

基于 RAG（检索增强生成）的多格式文档智能问答系统。支持 PDF/TXT/Markdown/DOCX 文档上传，使用 LangChain LCEL 构建链式管道，支持流式输出、对话记忆、文档摘要、多模型切换、RAG 质量评估。前端 Vue3 + 后端 FastAPI，Docker 一键部署。

## 技术栈

- **语言**: Python 3.10+ / TypeScript
- **RAG 框架**: LangChain LCEL（链式管道）
- **向量数据库**: ChromaDB（本地持久化，路径 `./chroma_db`）
- **文档解析**: PyPDF / TextLoader / UnstructuredMarkdownLoader / Docx2txtLoader
- **LLM**: OpenAI / DeepSeek / 通义千问 / 智谱 GLM / Ollama（多模型适配）
- **Embedding**: 智谱 embedding-3（可配置）
- **后端**: FastAPI + Uvicorn + SQLAlchemy（API 端点 + SSE 流式）
- **前端**: Vue3 + Vite + TypeScript + Pinia + Tailwind CSS
- **认证**: JWT (python-jose + bcrypt)
- **容器化**: Docker 多阶段构建（Node + Python）

## 项目结构

```
rag-document-qa/
├── api/                        # FastAPI 后端
│   ├── main.py                 # App 工厂 + CORS + 静态文件挂载
│   ├── routes.py               # REST + SSE 端点（含 /api/models）
│   ├── models.py               # Pydantic 模型（含 ModelInfo）
│   ├── auth.py                 # JWT 认证
│   ├── session.py              # 内存会话管理（SessionStore + UserStore）
│   ├── conversation_routes.py  # 对话管理 API
│   └── dependencies.py         # 共享依赖（cached embeddings）
├── frontend/                   # Vue3 前端
│   └── src/
│       ├── components/
│       │   ├── ChatView.vue         # 对话主视图
│       │   ├── ChatMessage.vue      # 消息渲染 + EvaluationPanel 集成
│       │   ├── ChatInput.vue        # 输入框 + 模型选择下拉框
│       │   ├── SourceCard.vue       # 引用卡片（页码 + 分数条）
│       │   ├── EvaluationPanel.vue  # RAG 评估面板（精确度/相关度/引用率）
│       │   ├── Sidebar.vue          # 侧边栏（对话列表 + 文档管理）
│       │   └── EmptyState.vue       # 空状态欢迎页
│       ├── stores/
│       │   ├── chat.ts              # 对话状态（含模型选择）
│       │   ├── conversation.ts      # 对话 CRUD
│       │   ├── auth.ts              # 认证状态
│       │   ├── theme.ts             # 主题切换
│       │   └── toast.ts             # 通知提示
│       ├── services/api.ts          # API 客户端（含 SSE 流式）
│       └── types/index.ts           # TypeScript 接口
├── rag/                        # RAG 核心模块（框架无关）
│   ├── loader.py               # 多格式文档加载（LOADER_MAP 策略模式）
│   ├── splitter.py             # 中文感知文本分割
│   ├── embeddings.py           # Embedding + ChromaDB 向量库管理
│   ├── retriever.py            # 余弦相似度检索器（similarity_score_threshold）
│   ├── chain.py                # LCEL 问答链 + 文档摘要（支持 model_name）
│   ├── llm_factory.py          # 多模型适配工厂（MODEL_REGISTRY）
│   └── evaluation.py           # RAG 质量评估引擎
├── database/                   # 数据库层（SQLAlchemy + SQLite）
│   ├── models.py               # ORM 模型（users/conversations/messages/documents）
│   ├── connection.py           # 数据库连接（默认 SQLite）
│   └── crud.py                 # CRUD 操作
├── config.py                   # 集中配置（环境变量解析）
├── Dockerfile                  # 多阶段构建
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── .env.example                # 环境变量模板
```

## 启动方式

```bash
# 本地启动
cp .env.example .env   # 编辑填入至少一个 LLM Provider 的 API Key
pip install -r requirements.txt

# 启动后端
uvicorn api.main:app --reload --port 8000

# 启动前端（另一个终端）
cd frontend && npm install && npm run dev

# Docker 启动
docker-compose up -d
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/models` | 获取可用 LLM 模型列表 |
| `POST` | `/api/upload` | 上传文档（multipart/form-data） |
| `GET` | `/api/status` | 获取当前会话状态 |
| `DELETE` | `/api/document/{doc_id}` | 删除单个文档 |
| `POST` | `/api/chat` | SSE 流式问答（支持 model 参数 + evaluation 返回） |
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录 |
| `GET` | `/api/conversations` | 获取对话列表 |
| `POST` | `/api/conversations` | 创建新对话 |
| `GET` | `/api/documents` | 获取用户文档列表 |

## 架构流程

```
文档上传 → loader.py 解析 → splitter.py 分块 → embeddings.py 向量化 → ChromaDB 存储
                                                                            ↓
用户提问 → API 接收 → retriever.py 检索 → chain.py LCEL 链 → SSE 流式回答
                                            ↓                              ↓
                                    llm_factory.py 模型选择      evaluation.py 质量评估
                                                                            ↓
                                                                  引用来源 + 评估指标
```

## 关键模块说明

### llm_factory.py — 多模型适配

- `MODEL_REGISTRY`: 模型注册表，包含所有支持的模型元数据
- `PROVIDER_CONFIG`: Provider 配置（base_url、api_key_env）
- `create_llm(model_name)`: 根据模型名创建 ChatOpenAI 实例
- `get_available_models()`: 返回可用模型列表（检查 API Key 是否配置）
- 所有 Provider 统一使用 ChatOpenAI 接口，通过 base_url 区分

### evaluation.py — RAG 评估引擎

- `evaluate_retrieval(source_docs, scores)`: 检索质量评估（精确度、平均分）
- `evaluate_citation_quality(answer, source_docs)`: 引用质量评估
- `format_evaluation_for_sse()`: 格式化为 SSE 事件数据
- 评估指标随 `/api/chat` 的 `done` 事件返回

### chain.py — LCEL 问答链

- `create_qa_chain(retriever, model_name)`: RAG 模式问答链
- `create_direct_chain(model_name)`: 直接对话模式（无检索）
- `summarize_document(docs, model_name)`: 文档摘要生成
- 返回 `ChainWithSources` 对象，支持 `.invoke()` 和 `.stream()`

## 关键配置（config.py，全部可通过 .env 覆盖）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| OPENAI_API_KEY | — | OpenAI API Key |
| DEEPSEEK_API_KEY | — | DeepSeek API Key |
| QWEN_API_KEY | — | 通义千问 API Key |
| ZHIPU_API_KEY | — | 智谱 API Key |
| LLM_MODEL | gpt-4o-mini | 默认 LLM 模型 |
| EMBEDDING_MODEL | embedding-3 | Embedding 模型 |
| CHUNK_SIZE | 500 | 文本分块大小 |
| CHUNK_OVERLAP | 50 | 分块重叠长度 |
| TOP_K | 4 | 检索返回文档块数 |
| TEMPERATURE | 0.3 | LLM 生成温度 |
| SIMILARITY_THRESHOLD | 0.5 | 相似度阈值 |
| CHROMA_PERSIST_DIR | ./chroma_db | ChromaDB 路径 |

## 开发注意事项

- `.env` 包含 API Key，已加入 `.gitignore`，不要提交
- rag/ 模块不依赖任何 Web 框架，可独立测试和复用
- chain.py 的 `create_qa_chain` 返回的对象支持 `.invoke()` 和 `.stream()`
- `summarize_document(docs)` 使用 LLM 生成文档摘要
- loader.py 使用 `LOADER_MAP` 策略模式，新增格式只需添加映射
- Prompt 模板含 `{chat_history}` 变量，最近 5 轮对话自动注入
- 测试用例不需要 OpenAI API key
- CI 使用 ruff 检查 + pytest 测试
- 前端开发时 Vite 在 5173 端口运行，代理 API 到 8000 端口
- 生产模式下 FastAPI 同时服务 API 和 Vue 静态文件
- 多模型支持：所有 Provider 兼容 OpenAI API 格式，统一使用 ChatOpenAI
- 前端模型选择器在 ChatInput.vue 中，模型状态存在 chat.ts store
- RAG 评估是轻量级的（基于检索分数），不额外调用 LLM
