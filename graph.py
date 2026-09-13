from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
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
        SystemMessage("You are web research agent." \
        "You must use web_search agent to research about user's question." \
        "Do not answer using your internal knowledge where the question requires" \
        "you to respond with current, recent or factual information." \
        "Use search result for additional searches or evidence and " \
        "use the search again if the information is not sufficient."),
        HumanMessage("\n".join(state["research_questions"])),
        *state["messages"]
    ])
    return {
        "messages": [response],
        "research_results": response.content
    }

def summarizer(state: ResearchState):
    response = summarizer_model.invoke([
        SystemMessage("You are summarizing agent." \
        f"Your task is to summarizer the answers for the question {state["question"]} so it can" \
        "withhold the meaning of the original question. The response should be well written" \
        "like blogs where the sub-headings are the sub-questions and the points." \
        "Don't start with here is your summary just start with main question and then the summmary."),
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

checkpoint = InMemorySaver()
graph = graph.compile(checkpointer = checkpoint)


