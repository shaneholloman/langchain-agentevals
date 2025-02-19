from agentevals.graph_trajectory.utils import (
    aextract_langgraph_trajectory_from_thread,
)
from agentevals.graph_trajectory.strict import graph_trajectory_strict_match_async

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_core.tools import tool

import pytest


@tool
def search(query: str):
    """Call to surf the web."""
    user_answer = interrupt("Tell me the answer to the question.")
    return user_answer


tools = [search]


@pytest.mark.langsmith
@pytest.mark.asyncio
async def test_trajectory_match():
    checkpointer = MemorySaver()
    graph = create_react_agent(
        model="gpt-4o-mini",
        checkpointer=checkpointer,
        tools=[search],
    )
    await graph.ainvoke(
        {"messages": [{"role": "user", "content": "what's the weather in sf?"}]},
        config={"configurable": {"thread_id": "1"}},
    )
    await graph.ainvoke(
        Command(resume="It is rainy and 70 degrees!"),
        config={"configurable": {"thread_id": "1"}},
    )
    extracted_trajectory = await aextract_langgraph_trajectory_from_thread(
        graph, {"configurable": {"thread_id": "1"}}
    )
    reference_trajectory = {
        "results": [],
        "steps": [["__start__", "agent", "tools", "__interrupt__"], ["agent"]],
    }
    res = await graph_trajectory_strict_match_async(
        outputs=extracted_trajectory["outputs"],
        reference_outputs=reference_trajectory,
    )
    assert res["score"]
