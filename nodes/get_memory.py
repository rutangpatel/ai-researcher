from langgraph.config import get_store

def read_memory(state):
    store = get_store()

    result = store.get(
        ("research", ),
        "last_question"
    )

    if result:
        return {
            "memory_context": result.value["question"]
        }

    return {"memory_context": ""}