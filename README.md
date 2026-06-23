# RAG Document QA

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-LCEL-green.svg)](https://langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue3-3.5+-42b883.svg)](https://vuejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 RAG（Retrieval-Augmented Generation）的多格式文档智能问答系统。上传文档，系统自动解析、向量化，然后基于文档内容进行多轮对话问答，回答附带原文引用和 RAG 质量评估。

## ✨ Features

- **多格式支持** — PDF、TXT、Markdown、DOCX 文档上传
- **多模型适配** — 支持 OpenAI / DeepSeek / 通义千问 / 智谱 GLM / MiMo / Ollama 本地模型，前端动态切换
- **LCEL 管道** — 基于 LangChain LCEL 构建 RAG 链，原生支持流式输出
- **对话记忆** — 多轮对话上下文记忆（最近 5 轮），支持追问
- **引用溯源** — 结构化引用标记，附带页码、相关度分数、文档来源
- **RAG 评估** — 检索精确度、平均相关度、引用覆盖率可视化面板
- **文档摘要** — LLM 自动生成 3-5 句文档摘要
- **用户系统** — JWT 认证，多用户隔离的知识库，支持头像上传、密码修改
- **知识库隔离** — 每个用户独立的向量库，重新登录后知识库自动恢复
- **对话管理** — 多对话创建、切换、重命名、删除，支持单条消息删除
- **临时文件** — 对话框内上传临时文件（按对话隔离，不入库）
- **模型标识** — 回答显示实际使用的模型名称（MiMo / GPT / DeepSeek 等）
- **系统提示词** — 用户可自定义系统提示词
- **前后端分离** — FastAPI 后端 + Vue3 前端，SSE 流式输出
- **Docker 部署** — 多阶段构建，一键容器化部署

## 🏗 Tech Stack

| 组件 | 技术 |
|------|------|
| RAG 框架 | LangChain LCEL |
| 向量数据库 | ChromaDB（按用户隔离集合） |
| LLM | OpenAI / DeepSeek / 通义千问 / 智谱 / MiMo / Ollama（可切换） |
| Embedding | 智谱 embedding-3（可配置） |
| 后端 | FastAPI + Uvicorn + SQLAlchemy |
| 前端 | Vue3 + Vite + TypeScript + Pinia |
| 认证 | JWT (python-jose + bcrypt) |
| 容器化 | Docker 多阶段构建（Node + Python） |

## 📐 Architecture

```
用户上传文档 (PDF/TXT/MD/DOCX)
    ↓
loader.py 解析 + 页码元数据提取
    ↓
splitter.py 中文感知分块（500字/块, 50字重叠）
    ↓
embeddings.py 向量化 → ChromaDB 持久化存储（按用户隔离集合）
    ↓
用户提问 → retriever.py 余弦相似度 Top-4 检索
    ↓
chain.py LCEL 链 → 多模型适配 → SSE 流式回答
    ↓
evaluation.py RAG 质量评估 → 引用来源 + 评估指标
```

## 🚀 Quick Start

### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，配置以下内容：
```

**LLM 配置（至少配置一个）：**
- `OPENAI_API_KEY` — OpenAI
- `DEEPSEEK_API_KEY` — DeepSeek
- `QWEN_API_KEY` — 通义千问
- `ZHIPU_API_KEY` — 智谱 GLM
- Ollama 本地模型无需 Key

**Embedding 配置（必须）：**
- `EMBEDDING_API_KEY` — 智谱 embedding-3 的 API Key
- `EMBEDDING_API_BASE` — 智谱 API 地址

### 3. 启动应用

```bash
# 启动后端
uvicorn api.main:app --reload --port 8000

# 启动前端（另一个终端）
cd frontend && npm run dev
```

浏览器打开 http://localhost:5173

## 🐳 Docker 部署

```bash
# 配置 .env 文件后
docker-compose up -d
```

访问 http://localhost:8000

## 📁 Project Structure

```
rag-document-qa/
├── api/                        # FastAPI 后端
│   ├── main.py                 # App 工厂 + CORS + 静态文件挂载
│   ├── routes.py               # REST + SSE 端点
│   ├── models.py               # Pydantic 模型
│   ├── auth.py                 # JWT 认证 + 用户管理
│   ├── session.py              # 内存会话管理（按用户隔离）
│   ├── conversation_routes.py  # 对话管理 API
│   └── dependencies.py         # 共享依赖
├── frontend/                   # Vue3 前端
│   └── src/
│       ├── components/         # UI 组件
│       │   ├── ChatView.vue        # 对话主视图
│       │   ├── ChatMessage.vue     # 消息渲染 + 引用标记 + 模型名
│       │   ├── ChatInput.vue       # 输入框 + 模型选择器
│       │   ├── SourceCard.vue      # 引用来源卡片（含分数）
│       │   ├── EvaluationPanel.vue # RAG 评估面板
│       │   └── Sidebar.vue         # 侧边栏（对话 + 文档）
│       ├── stores/             # Pinia 状态管理
│       ├── services/           # API 客户端（含 SSE）
│       └── types/              # TypeScript 接口
├── rag/                        # RAG 核心模块（框架无关）
│   ├── loader.py               # 多格式文档加载
│   ├── splitter.py             # 中文感知文本分割
│   ├── embeddings.py           # Embedding + ChromaDB（按用户隔离）
│   ├── retriever.py            # 余弦相似度检索器
│   ├── chain.py                # LCEL 问答链 + 文档摘要
│   ├── llm_factory.py          # 多模型适配工厂
│   └── evaluation.py           # RAG 质量评估引擎
├── database/                   # 数据库层（SQLAlchemy + SQLite）
│   ├── models.py               # ORM 模型
│   ├── connection.py           # 数据库连接 + 自动迁移
│   └── crud.py                 # CRUD 操作
├── config.py                   # 集中配置
├── Dockerfile                  # 多阶段构建
├── docker-compose.yml
└── .env.example                # 环境变量模板
```

## 🔌 API Endpoints

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/upload` | 上传文档到知识库（永久存储） |
| `POST` | `/api/upload/temp` | 上传临时文件（按对话隔离） |
| `GET` | `/api/status` | 获取当前会话状态 |
| `DELETE` | `/api/document/{doc_id}` | 删除单个文档 |
| `POST` | `/api/chat` | SSE 流式问答（支持模型选择 + 评估） |
| `GET` | `/api/models` | 获取可用模型列表 |

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录 |
| `GET` | `/api/auth/me` | 获取当前用户信息 |
| `POST` | `/api/auth/change-password` | 修改密码 |
| `POST` | `/api/auth/avatar` | 上传头像 |
| `GET/PUT` | `/api/auth/settings` | 获取/更新用户设置（系统提示词） |

### 对话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/conversations` | 获取对话列表 |
| `POST` | `/api/conversations` | 创建新对话 |
| `GET` | `/api/conversations/{id}` | 获取对话详情（含消息） |
| `PATCH` | `/api/conversations/{id}` | 更新对话标题 |
| `DELETE` | `/api/conversations/{id}` | 删除对话 |
| `DELETE` | `/api/conversations/{id}/messages/{msg_id}` | 删除单条消息 |

### 文档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/documents` | 获取用户文档列表 |
| `GET` | `/api/documents/{doc_id}` | 获取文档详情 |
| `DELETE` | `/api/documents/{doc_id}` | 删除文档（DB + 向量库 + 文件） |
| `GET` | `/api/documents/{doc_id}/content` | 获取文档内容预览 |

## ⚙️ Configuration

所有配置可通过环境变量或 `.env` 文件覆盖：

### LLM Provider

| 参数 | 默认值 | 说明 |
|------|--------|------|
| OPENAI_API_KEY | — | OpenAI API Key |
| OPENAI_API_BASE | https://api.openai.com/v1 | OpenAI API 地址 |
| DEEPSEEK_API_KEY | — | DeepSeek API Key |
| QWEN_API_KEY | — | 通义千问 API Key |
| ZHIPU_API_KEY | — | 智谱 GLM API Key |
| LLM_MODEL | gpt-4o-mini | 默认 LLM 模型 |

### Embedding

| 参数 | 默认值 | 说明 |
|------|--------|------|
| EMBEDDING_API_KEY | — | Embedding API Key（独立于 LLM） |
| EMBEDDING_API_BASE | https://open.bigmodel.cn/api/paas/v4 | Embedding API 地址 |
| EMBEDDING_MODEL | embedding-3 | Embedding 模型 |

### RAG 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| CHUNK_SIZE | 500 | 文本块大小 |
| CHUNK_OVERLAP | 50 | 文本块重叠 |
| TOP_K | 4 | 检索返回数量 |
| TEMPERATURE | 0.3 | LLM 温度 |
| SIMILARITY_THRESHOLD | 0.3 | 相似度阈值 |
| CHROMA_PERSIST_DIR | ./chroma_db | ChromaDB 存储路径 |

### 其他

| 参数 | 默认值 | 说明 |
|------|--------|------|
| CORS_ORIGINS | http://localhost:5173,... | CORS 允许的源 |
| JWT_SECRET_KEY | rag-qa-secret-key-... | JWT 密钥（生产环境请更换） |
| DATABASE_URL | sqlite:///./data/rag_qa.db | 数据库连接 |

## 🧪 Development

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码检查
ruff check .
ruff format --check .
```

## 📄 License

[MIT](LICENSE)
