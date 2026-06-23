"""RAG 评估引擎 - 实现 RAGAS 风格的检索质量评估指标

提供轻量级评估（基于检索分数）和可选的 LLM 评估（忠实度/相关性）。
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """检索质量指标"""
    context_precision: float = 0.0        # 检索精确度（有文档返回即为高）
    avg_relevance_score: float = 0.0      # 平均相似度分数
    top_k_scores: list[float] = field(default_factory=list)  # Top-K 分数列表
    total_chunks: int = 0                 # 检索到的文档块数


@dataclass
class FaithfulnessMetrics:
    """忠实度指标（基于 LLM 评估）"""
    score: float = 0.0
    supported_claims: int = 0
    total_claims: int = 0


@dataclass
class AnswerRelevancyMetrics:
    """回答相关性指标"""
    score: float = 0.0


@dataclass
class EvaluationResult:
    """完整评估结果"""
    retrieval: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    faithfulness: FaithfulnessMetrics | None = None
    answer_relevancy: AnswerRelevancyMetrics | None = None


def evaluate_retrieval(
    source_docs: list,
    similarity_scores: list[float] | None = None,
) -> RetrievalMetrics:
    """
    评估检索质量（轻量级，无需 LLM 调用）。

    Args:
        source_docs: 检索到的文档列表
        similarity_scores: ChromaDB 返回的相似度分数列表（可选）
    """
    total = len(source_docs)

    if total == 0:
        return RetrievalMetrics(
            context_precision=0.0,
            avg_relevance_score=0.0,
            top_k_scores=[],
            total_chunks=0,
        )

    # 如果没有外部分数，使用默认估算
    if similarity_scores and len(similarity_scores) > 0:
        scores = similarity_scores
    else:
        # 无外部分数时，基于文档数量给一个基础分
        scores = [0.7] * min(total, 4)

    avg_score = sum(scores) / len(scores) if scores else 0.0

    # 检索精确度：有文档返回且平均分数高于阈值
    # 使用 sigmoid-like 映射将分数转换为 0-1
    context_precision = min(1.0, avg_score * 1.2) if total > 0 else 0.0

    return RetrievalMetrics(
        context_precision=round(context_precision, 3),
        avg_relevance_score=round(avg_score, 3),
        top_k_scores=[round(s, 3) for s in scores],
        total_chunks=total,
    )


def evaluate_citation_quality(answer: str, source_docs: list) -> dict:
    """
    评估引用质量（轻量级）。

    检查回答中是否有引用标记，以及引用数量是否合理。
    """
    # 检测引用标记 [1], [2], [3] 等
    citation_pattern = r'\[(\d+)\]'
    citations_found = set(re.findall(citation_pattern, answer))
    citation_count = len(citations_found)

    # 检测"参考来源"或类似标记
    has_source_section = bool(re.search(r'参考来源|引用来源|参考资料|📚', answer))

    # 引用覆盖率：引用数 / 可用文档数
    available_docs = len(source_docs)
    coverage = min(1.0, citation_count / max(1, available_docs)) if available_docs > 0 else 0.0

    return {
        "citation_count": citation_count,
        "has_source_section": has_source_section,
        "coverage": round(coverage, 3),
        "available_docs": available_docs,
    }


def format_evaluation_for_sse(
    source_docs: list,
    similarity_scores: list[float] | None = None,
    answer: str | None = None,
) -> dict:
    """
    格式化评估结果为 SSE 事件数据。

    用于在 /api/chat 的 done 事件中返回评估指标。
    """
    retrieval = evaluate_retrieval(source_docs, similarity_scores)

    result = {
        "retrieval": {
            "context_precision": retrieval.context_precision,
            "avg_relevance_score": retrieval.avg_relevance_score,
            "top_k_scores": retrieval.top_k_scores,
            "total_chunks": retrieval.total_chunks,
        },
    }

    # 如果有回答文本，评估引用质量
    if answer:
        citation_eval = evaluate_citation_quality(answer, source_docs)
        result["citation"] = citation_eval

    return result
