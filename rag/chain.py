import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import DIRECT_CHAT_PROMPT, LLM_MODEL, OPENAI_API_BASE, OPENAI_API_KEY, QA_PROMPT, TEMPERATURE

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """请用 3-5 句话概括以下文档的主要内容，语言简洁明了：

{content}

摘要："""


def format_docs(docs) -> str:
    """将检索到的文档格式化为上下文字符串"""
    return "\n\n".join(doc.page_content for doc in docs)


def summarize_document(docs) -> str:
    """使用 LLM 生成文档摘要（取前 3000 字符）"""
    content = "\n\n".join(doc.page_content for doc in docs)[:3000]
    if not content.strip():
        return "（文档内容为空）"

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0.3,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
    )
    prompt = PromptTemplate(template=SUMMARY_PROMPT, input_variables=["content"])
    chain = prompt | llm | StrOutputParser()

    try:
        summary = chain.invoke({"content": content})
        logger.info("文档摘要生成成功")
        return summary
    except Exception as e:
        logger.warning(f"摘要生成失败: {e}")
        return "（摘要生成失败）"


def create_qa_chain(retriever):
    """创建 RAG 问答链（LCEL）"""
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        streaming=True,
    )

    prompt = PromptTemplate(
        template=QA_PROMPT,
        input_variables=["context", "question", "chat_history"],
    )

    generate_chain = prompt | llm | StrOutputParser()

    def _prepare(input_dict: dict) -> tuple[str, str, list]:
        """提取 question、chat_history，执行检索，返回 (question, chat_history, source_docs)"""
        question = input_dict["question"]
        chat_history = input_dict.get("chat_history", "")
        source_docs = retriever.invoke(question)
        return question, chat_history, source_docs

    def invoke(input_dict: dict) -> dict:
        question, chat_history, source_docs = _prepare(input_dict)
        context = format_docs(source_docs)
        answer = generate_chain.invoke(
            {
                "context": context,
                "question": question,
                "chat_history": chat_history,
            }
        )
        return {"result": answer, "source_documents": source_docs}

    def stream(input_dict: dict):
        """流式生成回答，返回 (chunks_generator, source_docs)"""
        question, chat_history, source_docs = _prepare(input_dict)
        context = format_docs(source_docs)

        def chunk_generator():
            for chunk in generate_chain.stream(
                {
                    "context": context,
                    "question": question,
                    "chat_history": chat_history,
                }
            ):
                yield chunk

        return chunk_generator(), source_docs

    class ChainWithSources:
        pass

    ChainWithSources.invoke = staticmethod(invoke)
    ChainWithSources.stream = staticmethod(stream)

    return ChainWithSources()


def create_direct_chain():
    """创建直接对话链（无 RAG 检索）"""
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        streaming=True,
    )

    prompt = PromptTemplate(
        template=DIRECT_CHAT_PROMPT,
        input_variables=["question", "chat_history"],
    )

    generate_chain = prompt | llm | StrOutputParser()

    def _invoke(input_dict: dict) -> dict:
        question = input_dict["question"]
        chat_history = input_dict.get("chat_history", "")
        answer = generate_chain.invoke({"question": question, "chat_history": chat_history})
        return {"result": answer, "source_documents": []}

    def _stream(input_dict: dict):
        """流式生成回答，返回 (chunks_generator, empty_source_docs)"""
        question = input_dict["question"]
        chat_history = input_dict.get("chat_history", "")

        def chunk_generator():
            for chunk in generate_chain.stream({"question": question, "chat_history": chat_history}):
                yield chunk

        return chunk_generator(), []

    class DirectChain:
        pass

    DirectChain.invoke = staticmethod(_invoke)
    DirectChain.stream = staticmethod(_stream)

    return DirectChain()
