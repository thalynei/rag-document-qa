import logging

from langchain_community.vectorstores import Chroma
from langchain_core.retrievers import BaseRetriever

from config import SIMILARITY_THRESHOLD, TOP_K

logger = logging.getLogger(__name__)


def get_retriever(vectorstore: Chroma, k: int = TOP_K) -> BaseRetriever:
    """创建检索器（带相似度阈值过滤）"""
    logger.info(f"创建检索器: Top-{k}, 阈值={SIMILARITY_THRESHOLD}")
    return vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": k,
            "score_threshold": SIMILARITY_THRESHOLD,
        },
    )
