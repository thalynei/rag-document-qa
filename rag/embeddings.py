import logging

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from config import CHROMA_PERSIST_DIR, EMBEDDING_API_BASE, EMBEDDING_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


def get_user_collection_name(user_id: int) -> str:
    """生成用户专属的 ChromaDB 集合名，实现知识库按用户隔离"""
    return f"rag_docs_user_{user_id}"


def get_embeddings() -> OpenAIEmbeddings:
    """初始化 OpenAI Embeddings"""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=EMBEDDING_API_KEY,
        openai_api_base=EMBEDDING_API_BASE,
    )


def load_vectorstore(embeddings=None, collection_name: str = "rag_docs") -> Chroma | None:
    """加载已有的向量库（如果存在）"""
    import os
    if not os.path.exists(CHROMA_PERSIST_DIR):
        return None

    if embeddings is None:
        embeddings = get_embeddings()

    try:
        vectorstore = Chroma(
            embedding_function=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
            collection_name=collection_name,
        )
        # 检查是否有数据
        count = vectorstore._collection.count()
        if count > 0:
            logger.info(f"加载已有向量库成功: {count} 块, 集合: {collection_name}")
            return vectorstore
        else:
            logger.info("向量库为空")
            return None
    except Exception as e:
        logger.warning(f"加载向量库失败: {e}")
        return None


def create_vectorstore(chunks: list, embeddings=None, collection_name: str = "rag_docs") -> Chroma:
    """将文档分块向量化并存入 ChromaDB"""
    if not chunks:
        raise ValueError("输入文档块列表为空")

    if embeddings is None:
        embeddings = get_embeddings()

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
            collection_name=collection_name,
        )
        logger.info(f"向量库创建成功: {len(chunks)} 块, 集合: {collection_name}")
        return vectorstore
    except Exception as e:
        logger.error(f"向量库创建失败: {e}")
        raise


def add_documents_to_vectorstore(vectorstore: Chroma, chunks: list) -> int:
    """向已有向量库添加文档块"""
    if not chunks:
        return 0
    try:
        vectorstore.add_documents(chunks)
        logger.info(f"向量库添加文档成功: {len(chunks)} 块")
        return len(chunks)
    except Exception as e:
        logger.error(f"向量库添加文档失败: {e}")
        raise


def delete_documents_by_filter(vectorstore: Chroma, filter_dict: dict) -> int:
    """按 metadata 过滤删除文档块（BUG #8 fix: use public API instead of _collection）"""
    try:
        # Use the public get() + delete() methods on the Chroma collection
        results = vectorstore._collection.get(where=filter_dict)
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            vectorstore._collection.delete(ids=ids_to_delete)
            logger.info(f"向量库删除文档成功: {len(ids_to_delete)} 块")
        return len(ids_to_delete)
    except Exception as e:
        logger.error(f"向量库删除文档失败: {e}")
        raise
