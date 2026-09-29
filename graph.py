from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.messages import SystemMessage, HumanMessage
from state import ResearchState
from langchain_typesafe import Choice
from models.jev import router
from nodes.chat.basic_chat import chat
from nodes.memory.memory_model import memory_model
from nodes.research.planner import planning_model
from nodes.research.researcher import research_model
from tools.search import web_search
from nodes.research.summarizer import summarizer_model
from nodes.memory.store_memory import save_memory
from nodes.memory.get_memory import read_memory

# Classifier determines who should answer the user query
def classifier(state: ResearchState):

    memory_context = state.get("memory_context", [])

    previous_question = "\n".join(
        f"{item["question"]} (similarity: {item["score"]:.2f})"
        for item in memory_context
    )

    response = router.invoke({
            "state": (
                f"Current user query:\n"
                f"{state["question"]} \n\n"
                f"Previous user interactions\n"
                f"{previous_question}"
            ),
            "questions": {
                "mode": Choice(
                    instructions = "Choose who should answer the user query.",
                    criteria = {
                        "memory": "Use when the previous interaction directly answers or helps answer the current query.",
                        "chat": "Use for general conversation or questions that do not require web research.",
                        "research": "Use when the query requires current, factual, or web-based information."
                    }
                )
            }
        }
    )
    return {"mode": response.choices["mode"].choice.lower()}

def route_query(state: ResearchState):
    mode = state["mode"]

    if mode == "memory" and not state.get("memory_context"):
        mode = "chat"
    if mode in ("memory", "chat", "research"):
        return mode
    raise ValueError(
        f"Jev returned invalid mode: {mode}"
    )

def memory_response(state: ResearchState):
    memories = state.get("memory_context", [])

    if not memories:
        raise ValueError(
            "Memory route selected but no memory found."
        )

    memory_text = "\n\n".join(
        f"Previous question: {m['question']}\nPrevious answer: {m['answer']}"
        for m in memories
    )

    response = memory_model.invoke([
        SystemMessage("Answer the user question which should be clean and helpful" \
        "and it should be done using previous memory answer." \
        "Format your response in markdown using '##' for section headings where appropriate, not bold text."),
        HumanMessage(f"""Current question: {state["question"]} Previous answer: {memory_text}""")
    ])
    
    return {
        "summary": response.content
    }

def chat_response(state: ResearchState):
    response = chat.invoke([
        SystemMessage("Answer the question without using any web-search" \
        "Do not assume anything for which previous memory is required" \
        "Provide clear and helpful answer." \
        "Format your response in markdown using '##' for section headings where appropriate, not bold text."),
        HumanMessage(f"Current question: {state["question"]}")
    ])
    return {"summary": response.content}

# Research agents which uses web search for answering user query
# Planning agent
def planner(state: ResearchState):
    response = planning_model.invoke([
        SystemMessage("Break the user's question into independent research questions" \
        "that can be answered by searching the web." \
        "Do not ask the user for clarification or preferences." \
        "Each question should investigate a specific factual aspect " \
        "needed to answer the original question thoroughly."),
        HumanMessage(f"Current question: {state["question"]}")
    ])
    return {"research_questions": response.question}

# Research agent
def researcher(state: ResearchState):
    response = research_model.invoke([
        SystemMessage("You are web research agent." \
        "You must use web_search agent to research about user's question." \
        "Do not answer using your internal knowledge where the question requires" \
        "you to respond with current, recent or factual information."),
        HumanMessage(f"""Original questions: {state["question"]}
        Research questions:{"\n".join(state["research_questions"])}"""),
        *state.get("messages", [])
    ])
    return {
        "messages": [response],
        "research_results": response.content
    }

# Summarizing agent
def summarizer(state: ResearchState):
    response = summarizer_model.invoke([
        SystemMessage("You are summarizing agent." \
        f"Your task is to summarize the answers for the question {state["question"]} so it can" \
        "withhold the meaning of the original question. The response should be well written" \
        "like blogs where the sub-headings are the sub-questions and the points." \
        "Don't start with here is your summary just start summmary with an introduction to the problem." \
        "Format your response in markdown using '##' for section headings where appropriate, not bold text."),
        HumanMessage(state["research_results"])
    ])
    return {"summary": response.content}

graph = StateGraph(ResearchState)

graph.add_node("read_memory", read_memory)
graph.add_node("classifier", classifier)
graph.add_node("memory", memory_response)
graph.add_node("chat", chat_response)
graph.add_node("planner", planner)
graph.add_node("researcher", researcher)
graph.add_node("tools", ToolNode([web_search]))
graph.add_node("summarizer", summarizer)
graph.add_node("save_memory", save_memory)

graph.add_edge(START, "read_memory")
graph.add_edge("read_memory", "classifier")
graph.add_conditional_edges(
    "classifier",
    route_query,
    {
        "memory": "memory",
        "chat": "chat",
        "research": "planner"
    }
)
graph.add_edge("memory", END)
graph.add_edge("chat", "save_memory")
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
graph.add_edge("summarizer", "save_memory")
graph.add_edge("save_memory", END)