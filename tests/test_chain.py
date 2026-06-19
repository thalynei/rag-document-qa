"""chain.py 单元测试（不需要 OpenAI API key）"""

from rag.chain import format_docs


def test_format_docs_empty():
    assert format_docs([]) == ""


def test_format_docs_single():
    class FakeDoc:
        page_content = "hello world"

    assert format_docs([FakeDoc()]) == "hello world"


def test_format_docs_multiple():
    class FakeDoc:
        def __init__(self, text):
            self.page_content = text

    docs = [FakeDoc("aaa"), FakeDoc("bbb"), FakeDoc("ccc")]
    assert format_docs(docs) == "aaa\n\nbbb\n\nccc"
