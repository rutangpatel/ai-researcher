import uuid
import voyageai
import os
from langgraph.config import get_store

vo = voyageai.Client(api_key = os.environ.get("VOYAGE_API_KEY"))

def save_memory(state):
    store = get_store()
    memory_id = str(uuid.uuid4())
    store.put(
        ("research",),
        memory_id,
        {
            "question": state["question"],
            "embedding": vo.embed(state["question"], model = "voyage-4-lite").embeddings[0],
            "answer": state["summary"]
        }
    )

    return {}