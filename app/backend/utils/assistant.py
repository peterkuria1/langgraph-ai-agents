# utils/assistant.py
import uuid
from typing_extensions import TypedDict
from typing import Any

# langchain | langgraph
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.message import AnyMessage, add_messages


class AgentState(TypedDict):
    messages: list[AnyMessage]


class Assistant:
    """
    An agent that handles invoking a runnable object and managing retries based on the response.
    """

    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def should_retry(self, response: Any) -> bool:
        """
        Determines if the response warrants a retry.
        """
        return (
            not response.tool_calls and
            (not response.content or
             (isinstance(response.content, list) and not response.content[0].get('text')))
        )

    def update_state_for_retry(self, state: AgentState) -> AgentState:
        """
        Updates the agent's state for retry.
        """
        state["messages"].append("Respond with a valid output")
        return state

    async def __call__(self, state: AgentState, config: RunnableConfig) -> dict:
        """
        Invokes the runnable and handles retry logic until a valid response is returned.
        """
        response = await self.runnable.ainvoke(state)

        while self.should_retry(response):
            state = self.update_state_for_retry(state)
            response = await self.runnable.ainvoke(state)

        return {"messages": response}


def assistant_answer(app: Runnable, example: dict) -> dict:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    messages = app.invoke({"messages": [example["input"]]}, config)

    return {
        "response": messages["messages"][-1].content,
        "messages": messages
    }
