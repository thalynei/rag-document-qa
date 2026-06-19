# RAG Document QA

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-LCEL-green.svg)](https://langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue3-3.5+-42b883.svg)](https://vuejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 RAG（Retrieval-Augmented Generation）的多格式文档智能问答系统。上传文档，系统自动解析、向量化，然后基于文档内容进行多轮对话问答，回答附带原文引用。

## Features

- **多格式支持** — PDF、TXT、Markdown、DOCX 文档上传
- **LCEL 管道** — 基于 LangChain LCEL 构建 RAG 链，原生支持流式输出
- **对话记忆** — 多轮对话上下文记忆（最近 5 轮），支持追问
- **来源溯源** — 每条回答附带原文引用，可追溯到具体页码
- **文档摘要** — LLM 自动生成 3-5 句文档摘要
- **前后端分离** — FastAPI 后端 + Vue3 前端，SSE 流式输出
- **Docker 部署** — 多阶段构建，一键容器化部署

## Tech Stack

| 组件 | 技术 |
|------|------|
| RAG 框架 | LangChain LCEL |
| 向量数据库 | ChromaDB |
| LLM | OpenAI gpt-4o-mini |
| Embedding | OpenAI text-embedding-3-small |
| 后端 | FastAPI + Uvicorn |
| 前端 | Vue3 + Vite + TypeScript + Pinia + Tailwind CSS |
| 容器化 | Docker 多阶段构建（Node + Python） |

## Architecture

```
用户上传文档 (PDF/TXT/MD/DOCX)
    ↓
文档解析 + 页码元数据提取
    ↓
RecursiveCharacterTextSplitter 分块（500字/块, 50字重叠）
    ↓
OpenAI Embeddings 向量化 → ChromaDB 持久化存储
    ↓
用户提问 → 对话历史格式化 → 余弦相似度 Top-4 检索
    ↓
LCEL 链 (prompt | llm | StrOutputParser) → SSE 流式回答 + 引用来源
```

## Quick Start

### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

### 3. 启动应用

```bash
# 启动后端
uvicorn api.main:app --reload --port 8000

# 启动前端（另一个终端）
cd frontend && npm run dev
```

浏览器打开 http://localhost:5173

## Docker 部署

```bash
# 配置 .env 文件后
docker-compose up -d
```

访问 http://localhost:8000

## Project Structure

```
rag-pdf-qa/
├── api/                    # FastAPI 后端
│   ├── main.py             # App 工厂 + CORS + 静态文件挂载
│   ├── routes.py           # REST + SSE 端点
│   ├── models.py           # Pydantic 模型
│   ├── session.py          # 内存会话管理
│   └── dependencies.py     # 共享依赖
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── components/     # UI 组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── services/       # API 客户端
│   │   └── types/          # TypeScript 接口
│   └── vite.config.ts      # Vite + API 代理
├── rag/                    # RAG 核心模块（框架无关）
│   ├── loader.py           # 多格式文档加载（PDF/TXT/MD/DOCX）
│   ├── splitter.py         # 中文感知文本分割
│   ├── embeddings.py       # Embedding + ChromaDB 向量库管理
│   ├── retriever.py        # 余弦相似度检索器
│   └── chain.py            # LCEL 问答链 + 文档摘要
├── tests/                  # 单元测试
├── config.py               # 集中配置
├── Dockerfile              # 多阶段构建
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## API Endpoints

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/upload` | 上传文档（multipart/form-data） |
| `GET` | `/api/status` | 获取当前会话状态 |
| `DELETE` | `/api/document` | 清除当前文档 |
| `POST` | `/api/chat` | SSE 流式问答 |

## Configuration

所有配置可通过环境变量或 `.env` 文件覆盖：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| OPENAI_API_KEY | — | OpenAI API Key（必填） |
| OPENAI_API_BASE | https://api.openai.com/v1 | API 地址（支持代理） |
| LLM_MODEL | gpt-4o-mini | LLM 模型 |
| EMBEDDING_MODEL | text-embedding-3-small | Embedding 模型 |
| CHUNK_SIZE | 500 | 文本块大小 |
| CHUNK_OVERLAP | 50 | 文本块重叠 |
| TOP_K | 4 | 检索返回数量 |
| TEMPERATURE | 0.3 | LLM 温度 |
| CHROMA_PERSIST_DIR | ./chroma_db | ChromaDB 存储路径 |
| CORS_ORIGINS | http://localhost:5173,... | CORS 允许的源（逗号分隔） |

## Development

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码检查
ruff check .
ruff format --check .
```

## License

[MIT](LICENSE)
