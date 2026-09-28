from typing_extensions import TypedDict, NotRequired
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class ResearchState(TypedDict):
    question: str
    research_questions: NotRequired[list[str]]
    messages: NotRequired[Annotated[list[AnyMessage], add_messages]]
    research_results: NotRequired[list[str]]
    summary: NotRequired[str]
    mode: NotRequired[str]
    memory_context: NotRequired[list[dict]]