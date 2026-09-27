from langgraph.config import get_store

def save_memory(state):
    store = get_store()

    store.put(
        ("research", ),
        "last_question",
        {"question": state["question"]}
    )

    return {}