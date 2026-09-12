from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from state import ResearchState
from nodes.planner import planning_model
from nodes.researcher import research_model
from tools.search import web_search
from nodes.summarizer import summarizer_model

def planner(state: ResearchState):
    response = planning_model.invoke([
        SystemMessage("Break the user's question into independent research questions" \
        "that can be answered by searching the web." \
        "Do not ask the user for clarification or preferences." \
        "Each question should investigate a specific factual aspect " \
        "needed to answer the original question thoroughly."),
        HumanMessage(state["question"])
    ])
    return {"research_questions": response.question}

def researcher(state: ResearchState):
    response = research_model.invoke([
        SystemMessage("Research about the question provided using the web search tool provided to you"),
        HumanMessage("\n".join(state["research_questions"])),
        *state["messages"]
    ])
    return {
        "messages": [response],
        "research_results": response.content
    }

def summarizer(state: ResearchState):
    response = summarizer_model.invoke([
        SystemMessage("Summarize the content provided to you and make sure it is well defined and well articulated" \
        f"so it doesn't forget the meaning of the original question which is {state["question"]}"),
        AIMessage(state["research_results"])
    ])
    return {"summary": response.content}

graph = StateGraph(ResearchState)

graph.add_node("planner", planner)
graph.add_node("researcher", researcher)
graph.add_node("tools", ToolNode([web_search]))
graph.add_node("summarizer", summarizer)

graph.add_edge(START, "planner")
graph.add_edge("planner", "researcher")
graph.add_conditional_edges(
    "researcher", 
    tools_condition,
    {
        "tools": "tools",
        "__end__": "summarizer"
    }
)

graph.add_edge("tools", "researcher")
graph.add_edge("summarizer", END)

graph = graph.compile()


