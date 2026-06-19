"""loader.py 单元测试（不需要 OpenAI API key）"""

import pytest

from rag.loader import load_pdf


def test_load_unsupported_format_raises(tmp_path):
    fake_file = tmp_path / "test.xyz"
    fake_file.write_text("some content")
    with pytest.raises(ValueError, match="不支持的文件格式"):
        load_pdf(str(fake_file))


def test_load_nonexistent_file_raises():
    with pytest.raises(Exception):
        load_pdf("/nonexistent/file.pdf")


def test_load_txt_file(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("这是一段测试文本。\n第二行内容。")
    docs = load_pdf(str(txt_file), original_filename="test.txt")
    assert len(docs) >= 1
    assert docs[0].metadata["source"] == "test.txt"
    assert "page_label" in docs[0].metadata
