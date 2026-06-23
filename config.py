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
EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE", "https://open.bigmodel.cn/api/paas/v4")

# 多模型支持：不再强制要求 OPENAI_API_KEY，各 Provider 按需检查
# if not OPENAI_API_KEY:
#     raise RuntimeError("OPENAI_API_KEY is not set. Set it in your .env file or environment variables.")

# 默认模型（可通过 .env 覆盖）
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", LLM_MODEL)

# 可用模型列表（逗号分隔，空则使用 MODEL_REGISTRY 全量）
AVAILABLE_MODELS = os.getenv("AVAILABLE_MODELS", "")


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
SIMILARITY_THRESHOLD = _parse_float("SIMILARITY_THRESHOLD", "0.3")  # 相似度阈值（质谱 embedding 分数偏低，适当降低）

# ChromaDB 持久化路径
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# Prompt 模板
QA_PROMPT = """你是一个专业的文档问答助手，专注于帮助用户理解和分析文档内容。

## 核心职责
1. 基于检索到的文档内容准确回答用户问题
2. 提供信息溯源（引用文档来源页码）
3. 支持多轮对话，理解上下文

## 回答规范

### 情况1：用户问题与文档内容相关
- 基于文档内容回答，引用来源页码
- 示例："根据文档第X页的内容，..."

### 情况2：用户问题与文档内容无关或检索结果为空
- 说明"💡 知识库中暂未找到与该问题相关的文档"
- 基于通用知识回答，不显示参考来源

### 情况3：闲聊或通用问题
- 直接回答，不提及知识库

## 对话历史
{chat_history}

## 检索到的文档内容
{context}

## 用户问题
{question}

## 回答"""

DIRECT_CHAT_PROMPT = """你是一个智能文档问答助手，专注于帮助用户理解和分析文档。

## 你的能力
1. 回答一般性问题
2. 协助用户理解文档分析相关概念
3. 提供使用指导

## 回答规范
- 保持专业、友好、有条理
- 如果用户询问文档相关问题，建议他们上传文档以获得更精准的回答

## 对话历史
{chat_history}

## 用户问题
{question}

## 回答"""
