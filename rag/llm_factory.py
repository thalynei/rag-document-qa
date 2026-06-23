"""多模型适配工厂 - 支持 OpenAI / DeepSeek / 通义千问 / 智谱 / Ollama 等兼容 OpenAI API 的 Provider"""

import logging
import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """模型元数据"""
    id: str
    display_name: str
    provider: str
    max_tokens: int = 8192
    description: str = ""


# ─── 模型注册表 ───────────────────────────────────────────────────────────────

MODEL_REGISTRY: dict[str, ModelInfo] = {
    # OpenAI
    "gpt-4o-mini": ModelInfo("gpt-4o-mini", "GPT-4o Mini", "openai", 16384, "快速轻量模型"),
    "gpt-4o": ModelInfo("gpt-4o", "GPT-4o", "openai", 128000, "旗舰多模态模型"),
    "gpt-4.1-mini": ModelInfo("gpt-4.1-mini", "GPT-4.1 Mini", "openai", 1048576, "新一代快速模型"),
    # DeepSeek
    "deepseek-chat": ModelInfo("deepseek-chat", "DeepSeek V3", "deepseek", 8192, "深度求索通用模型"),
    "deepseek-reasoner": ModelInfo("deepseek-reasoner", "DeepSeek R1", "deepseek", 8192, "深度求索推理模型"),
    # 通义千问
    "qwen-plus": ModelInfo("qwen-plus", "通义千问 Plus", "qwen", 8192, "阿里云旗舰模型"),
    "qwen-turbo": ModelInfo("qwen-turbo", "通义千问 Turbo", "qwen", 8192, "阿里云快速模型"),
    # 智谱 GLM
    "glm-4-flash": ModelInfo("glm-4-flash", "GLM-4 Flash", "zhipu", 8192, "智谱快速模型"),
    "glm-4-plus": ModelInfo("glm-4-plus", "GLM-4 Plus", "zhipu", 8192, "智谱旗舰模型"),
    # Ollama 本地模型
    "qwen2.5:7b": ModelInfo("qwen2.5:7b", "Qwen2.5 7B (本地)", "ollama", 4096, "本地部署的通义千问"),
    "llama3.1:8b": ModelInfo("llama3.1:8b", "Llama 3.1 8B (本地)", "ollama", 4096, "Meta 开源模型"),
    "deepseek-r1:8b": ModelInfo("deepseek-r1:8b", "DeepSeek R1 8B (本地)", "ollama", 4096, "本地部署的推理模型"),
    # MiMo
    "mimo-v2.5": ModelInfo("mimo-v2.5", "MiMo V2.5", "mimo", 4096, "小米 MiMo 推理模型"),
    "mimo-v2.5-pro": ModelInfo("mimo-v2.5-pro", "MiMo V2.5 Pro", "mimo", 8192, "小米 MiMo 旗舰推理模型"),
}

# ─── Provider 配置 ────────────────────────────────────────────────────────────

PROVIDER_CONFIG: dict[str, dict] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "QWEN_API_KEY",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key_env": "ZHIPU_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": None,  # Ollama 不需要 API Key
    },
    "mimo": {
        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
}


def get_available_models() -> list[dict]:
    """返回所有可用模型列表（前端展示用）"""
    available = []
    for model_id, info in MODEL_REGISTRY.items():
        provider_conf = PROVIDER_CONFIG.get(info.provider, {})
        api_key_env = provider_conf.get("api_key_env")

        # 检查 API Key 是否配置（Ollama 不需要）
        if api_key_env and not os.getenv(api_key_env):
            # 回退到 OPENAI_API_KEY（兼容配置）
            if not os.getenv("OPENAI_API_KEY"):
                continue

        available.append({
            "id": info.id,
            "display_name": info.display_name,
            "provider": info.provider,
            "max_tokens": info.max_tokens,
            "description": info.description,
        })
    return available


def _resolve_api_key(provider: str) -> str | None:
    """解析 Provider 对应的 API Key"""
    provider_conf = PROVIDER_CONFIG.get(provider, {})
    api_key_env = provider_conf.get("api_key_env")

    if not api_key_env:
        return "ollama"  # Ollama 不需要 key，返回占位符

    # 优先使用 Provider 专用 Key
    key = os.getenv(api_key_env)
    if key:
        return key

    # 回退到 OPENAI_API_KEY（兼容只配置了一个 Key 的场景）
    fallback = os.getenv("OPENAI_API_KEY")
    if fallback:
        logger.debug(f"Provider {provider} 使用 OPENAI_API_KEY 回退")
        return fallback

    return None


def create_llm(
    model_name: str | None = None,
    temperature: float = 0.3,
    streaming: bool = True,
    max_tokens: int | None = None,
) -> ChatOpenAI:
    """
    根据模型名创建 LLM 实例。

    所有主流 LLM Provider 都兼容 OpenAI API 格式，
    统一使用 ChatOpenAI 通过 base_url 区分。
    """
    from config import LLM_MODEL, OPENAI_API_BASE, OPENAI_API_KEY, TEMPERATURE

    # 使用默认模型
    if not model_name or model_name not in MODEL_REGISTRY:
        model_name = LLM_MODEL
        base_url = OPENAI_API_BASE
        api_key = OPENAI_API_KEY
        if max_tokens is None:
            max_tokens = 4096  # 推理模型需要足够 token
    else:
        info = MODEL_REGISTRY[model_name]
        provider_conf = PROVIDER_CONFIG.get(info.provider, {})
        base_url = provider_conf.get("base_url", OPENAI_API_BASE)
        api_key = _resolve_api_key(info.provider) or OPENAI_API_KEY
        if max_tokens is None:
            max_tokens = info.max_tokens

    if not api_key:
        raise ValueError(f"模型 {model_name} 需要 API Key 但未配置")

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base=base_url,
        streaming=streaming,
        max_tokens=max_tokens,
    )

    logger.debug(f"创建 LLM 实例: {model_name} @ {base_url}")
    return llm
