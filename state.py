from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class ResearchState(TypedDict):
    question: str
    research_questions: list[str]
    messages: Annotated[list[AnyMessage], add_messages]
    research_results: list[str]
    summary: str