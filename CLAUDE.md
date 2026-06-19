# CLAUDE.md — RAG Document QA 项目指南

## 项目概述

基于 RAG（检索增强生成）的多格式文档智能问答系统。支持 PDF/TXT/Markdown/DOCX 文档上传，使用 LangChain LCEL 构建链式管道，支持流式输出、对话记忆、文档摘要。前端 Vue3 + 后端 FastAPI，Docker 一键部署。

## 技术栈

- **语言**: Python 3.10+ / TypeScript
- **RAG 框架**: LangChain LCEL（链式管道）
- **向量数据库**: ChromaDB（本地持久化，路径 `./chroma_db`）
- **文档解析**: PyPDF / TextLoader / UnstructuredMarkdownLoader / Docx2txtLoader
- **LLM**: OpenAI gpt-4o-mini（可配置）
- **Embedding**: OpenAI text-embedding-3-small（可配置）
- **后端**: FastAPI + Uvicorn（API 端点 + SSE 流式）
- **前端**: Vue3 + Vite + TypeScript + Pinia + Tailwind CSS
- **容器化**: Docker 多阶段构建（Node + Python）

## 项目结构

```
rag-pdf-qa/
├── api/                    # FastAPI 后端
│   ├── __init__.py
│   ├── main.py             # App 工厂 + CORS + 静态文件挂载
│   ├── routes.py           # REST + SSE 端点
│   ├── models.py           # Pydantic 模型
│   ├── session.py          # 内存会话管理
│   ├── dependencies.py     # 共享依赖
│   └── retriever_wrapper.py
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── App.vue         # 根布局
│   │   ├── main.ts         # 入口
│   │   ├── types/          # TS 接口
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── services/       # API 客户端（含 SSE）
│   │   └── components/     # UI 组件
│   ├── vite.config.ts      # Vite + API 代理
│   └── package.json
├── rag/                    # RAG 核心模块（框架无关）
│   ├── __init__.py         # logging 配置
│   ├── loader.py           # 多格式文档加载
│   ├── splitter.py         # 中文感知文本分割
│   ├── embeddings.py       # Embedding + ChromaDB
│   ├── retriever.py        # 余弦相似度检索器
│   └── chain.py            # LCEL 问答链 + 文档摘要
├── tests/                  # 单元测试（不需要 API key）
├── config.py               # 集中配置
├── Dockerfile              # 多阶段构建
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
├── LICENSE                 # MIT
└── 简历项目描述.md
```

## 启动方式

```bash
# 本地启动
cp .env.example .env   # 编辑填入 OPENAI_API_KEY
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
| `POST` | `/api/upload` | 上传文档（multipart/form-data） |
| `GET` | `/api/status` | 获取当前会话状态 |
| `DELETE` | `/api/document` | 清除当前文档 |
| `POST` | `/api/chat` | SSE 流式问答 |

## 架构流程

```
文档上传 → loader.py 解析 → splitter.py 分块 → embeddings.py 向量化 → ChromaDB 存储
                                                                            ↓
用户提问 → API 接收 → retriever.py 检索 → chain.py LCEL 链 → SSE 流式回答 + 引用来源
                                                                            ↓
                                                                    chain.py summarize → 文档摘要
```

## 关键配置（config.py，全部可通过 .env 覆盖）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| LLM_MODEL | gpt-4o-mini | LLM 模型 |
| EMBEDDING_MODEL | text-embedding-3-small | Embedding 模型 |
| CHUNK_SIZE | 500 | 文本分块大小 |
| CHUNK_OVERLAP | 50 | 分块重叠长度 |
| TOP_K | 4 | 检索返回文档块数 |
| TEMPERATURE | 0.3 | LLM 生成温度 |
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
