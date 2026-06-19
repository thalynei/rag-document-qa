import logging
import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

logger = logging.getLogger(__name__)

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".md": UnstructuredMarkdownLoader,
}

try:
    from langchain_community.document_loaders import Docx2txtLoader

    LOADER_MAP[".docx"] = Docx2txtLoader
except ImportError:
    pass


def _make_text_loader(file_path: str) -> TextLoader:
    """Create a TextLoader with encoding fallback for non-UTF-8 files (BUG #11 fix)."""
    try:
        return TextLoader(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 解码失败，尝试 GBK: {file_path}")
        return TextLoader(file_path, encoding="gbk", autodetect_encoding=True)


def load_pdf(file_path: str, original_filename: str = None) -> list:
    """加载文档，返回包含页码信息的文档列表（支持 pdf/txt/md/docx）"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        loader = _make_text_loader(file_path)
    else:
        loader_cls = LOADER_MAP.get(ext)
        if loader_cls is None:
            supported = ", ".join(list(LOADER_MAP.keys()) + [".txt"])
            raise ValueError(f"不支持的文件格式: {ext}。支持的格式: {supported}")
        loader = loader_cls(file_path)

    try:
        docs = loader.load()
    except Exception as e:
        logger.error(f"文档加载失败: {file_path}, 错误: {e}")
        raise

    if not docs:
        raise ValueError(f"文档为空或无法解析: {file_path}")

    display_name = original_filename or os.path.basename(file_path)
    for i, doc in enumerate(docs):
        page = doc.metadata.get("page", i)
        if isinstance(page, int):
            page += 1  # 页码从1开始
        doc.metadata["source"] = display_name
        doc.metadata["page_label"] = f"第{page}页"

    logger.info(f"文档加载成功: {display_name}, {len(docs)} 页")
    return docs
