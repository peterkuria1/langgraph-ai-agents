# utils/tools.py
import os
from typing import Any
from typing_extensions import TypedDict

# langchain | langgraph
from langchain_community.document_loaders import ArxivLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
import logging

# Quart-based logging setup
logging.basicConfig(level=logging.INFO)

def load_documents(query: str, load_max_docs: int, model_name: str = 'nomic-embed-text'):
    """
    Load documents based on the user query.
    """
    logging.info('---LOADING DOCS---')

    loader = ArxivLoader(query=query, load_max_docs=load_max_docs)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        length_function=len
    )

    new_docs = text_splitter.split_documents(documents=docs)
    embeddings = OllamaEmbeddings(model=model_name)
    db = Chroma.from_documents(new_docs, embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 3})
    return retriever


@tool
async def retrieve(state: str):
    """
    Retrieve documents.
    """
    logging.info('---RETRIEVE---')

    retriever = load_documents(state, 3)
    documents = retriever.get_relevant_documents(state)
    return {'messages': [state, documents]}


@tool
async def web_search(state: str):
    """
    Call web search.
    """
    logging.info('---WEB SEARCH---')

    try:
        tool = DuckDuckGoSearchResults()
        result = tool.invoke(state)
        return {'messages': [result]}
    except Exception as e:
        logging.error(f"Web search error: {e}")
        return {'messages': [f"Error: {str(e)}"]}


def handle_tool_error(state) -> dict:
    """
    Handle errors related to tool calls.
    """
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            {"content": f"Error: {repr(error)}\nPlease fix your mistakes.", "tool_call_id": tc["id"]}
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """
    Create a ToolNode with fallback.
    """
    return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")
