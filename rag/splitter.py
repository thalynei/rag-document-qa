import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE

logger = logging.getLogger(__name__)


def split_documents(docs: list[Document]) -> list[Document]:
    """将文档分块，保留元数据（页码等）"""
    if not docs:
        raise ValueError("输入文档列表为空")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    logger.info(f"文档分块完成: {len(docs)} 页 → {len(chunks)} 块")
    return chunks
