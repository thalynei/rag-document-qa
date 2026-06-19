import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embedding-3")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", OPENAI_API_KEY)
EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE", OPENAI_API_BASE)  # BUG #6 fix: consistent defaults

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Set it in your .env file or environment variables.")


def _parse_int(name: str, default: str) -> int:
    """Parse an integer env var with a descriptive error on failure (BUG #9 fix)."""
    raw = os.getenv(name, default)
    try:
        return int(raw)
    except ValueError:
        logger.warning(f"环境变量 {name}={raw!r} 不是有效整数，使用默认值 {default}")
        return int(default)


def _parse_float(name: str, default: str) -> float:
    """Parse a float env var with a descriptive error on failure (BUG #9 fix)."""
    raw = os.getenv(name, default)
    try:
        return float(raw)
    except ValueError:
        logger.warning(f"环境变量 {name}={raw!r} 不是有效浮点数，使用默认值 {default}")
        return float(default)


# RAG 参数
CHUNK_SIZE = _parse_int("CHUNK_SIZE", "500")
CHUNK_OVERLAP = _parse_int("CHUNK_OVERLAP", "50")
TOP_K = _parse_int("TOP_K", "4")
TEMPERATURE = _parse_float("TEMPERATURE", "0.3")
SIMILARITY_THRESHOLD = _parse_float("SIMILARITY_THRESHOLD", "0.5")  # 相似度阈值，低于此值的结果被视为不相关

# ChromaDB 持久化路径
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# Prompt 模板
QA_PROMPT = """你是 "RAG 智能文档问答助手"，一个专业的文档分析和问答系统。

## 你的身份
- 名称：RAG 智能文档问答助手
- 开发团队：AI 技术团队
- 核心能力：文档解析、智能问答、知识溯源

## 你的职责
1. 帮助用户理解和分析上传的文档
2. 基于文档内容回答用户问题
3. 提供准确的信息溯源（引用文档来源）
4. 支持多轮对话，理解上下文

## 回答规范

### 情况1：用户问题与检索到的文档内容相关
- 基于文档内容回答问题
- 在回答末尾添加"📚 参考来源"部分，引用相关文档的页码或段落
- 示例："根据文档第X页的内容，..."

### 情况2：用户问题与文档内容无关或检索结果为空
- 先说明"💡 知识库中暂未找到与该问题相关的文档"
- 然后基于你的通用知识回答用户的问题
- 不要显示"参考来源"部分

### 情况3：用户的问题是闲聊或通用问题
- 直接回答用户问题
- 不要提及知识库，不要显示"参考来源"部分

## 重要规则
- 只有当问题与文档内容有明确关联时，才显示参考来源
- 如果检索到的文档内容为空，直接基于通用知识回答
- 保持专业、准确、有条理

## 对话历史
{chat_history}

## 检索到的文档内容
{context}

## 用户问题
{question}

## 回答"""

DIRECT_CHAT_PROMPT = """你是 "RAG 智能文档问答助手"，一个专业的文档分析和问答系统。

## 你的身份
- 名称：RAG 智能文档问答助手
- 开发团队：AI 技术团队
- 核心能力：文档解析、智能问答、知识溯源

## 你的能力
1. 回答一般性问题
2. 协助用户理解文档分析相关概念
3. 提供使用指导

## 回答规范
- 如果用户问你是谁，请介绍自己是 "RAG 智能文档问答助手"
- 不要提及任何其他 AI 模型名称（如 MiMo、GPT 等）
- 保持专业、友好、有条理
- 如果用户询问文档相关问题，建议他们上传文档以获得更精准的回答

## 对话历史
{chat_history}

## 用户问题
{question}

## 回答"""
