# Import necessary libraries
import glob
from quart import Quart, render_template, request, session, redirect, url_for
import asyncio

import os

from utils.prompt_template import primary_assistant_prompt

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
# from langgraph.checkpoint.sqlite import SqliteSaver

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Initialize Quart app
app = Quart(__name__)
app.secret_key = os.getenv("QUART_APP_SECRET_KEY")


def create_graph():
    """
    Creates and compiles a state graph for managing the interaction between an assistant agent and tool nodes.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("assistant", Assistant(assistant))
    workflow.add_node("tools", create_tool_node_with_fallback(tools))

    # Add edges
    workflow.add_edge(START, "assistant")
    workflow.add_conditional_edges("assistant", tools_condition)
    workflow.add_edge("tools", "assistant")

    return workflow.compile()


async def run_workflow(inputs):
    """
    Asynchronously runs the workflow based on the provided inputs.
    """
    value = await session['workflow'].ainvoke(inputs)

    # sqlite3_conn = sqlite3.connect('checkpoints.sqlite')
    # sqlite3_memory_checkpoint = SqliteSaver(sqlite3_conn)
    # app = workflow.compile(checkpointer=sqlite3_memory_checkpoint)
    # final_state = app.invoke(
    #     {"messages": [HumanMessage(content='give me a few names of people who were pivotal in eradication of global slave trade. ')]},
    #     config={"configurable": {"thread_id": 1}}
    # )


    return value


@app.route('/', methods=['GET', 'POST'])
async def index():
    if 'log' not in session:
        session['log'] = ""

    if 'workflow' not in session:
        graph = create_graph()
        session['workflow'] = graph

    result = None
    if request.method == 'POST':
        prompt = (await request.form).get('query')
        inputs = {"messages": [prompt]}
        result = await run_workflow(inputs)

    return await render_template('index.html', result=result)


if __name__ == '__main__':
    app.run()
