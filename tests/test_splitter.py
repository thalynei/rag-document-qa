"""splitter.py 单元测试（不需要 OpenAI API key）"""

import pytest

from rag.splitter import split_documents


def test_split_empty_raises():
    with pytest.raises(ValueError, match="输入文档列表为空"):
        split_documents([])


def test_split_preserves_metadata():
    class FakeDoc:
        def __init__(self, text, metadata=None):
            self.page_content = text
            self.metadata = metadata or {}

    docs = [FakeDoc("a" * 1000, {"source": "test.pdf", "page": 1})]
    chunks = split_documents(docs)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.metadata.get("source") == "test.pdf"


def test_split_chunk_size_respected():
    class FakeDoc:
        def __init__(self, text):
            self.page_content = text
            self.metadata = {}

    docs = [FakeDoc("a" * 2000)]
    chunks = split_documents(docs)
    for chunk in chunks:
        assert len(chunk.page_content) <= 600  # chunk_size + some tolerance
