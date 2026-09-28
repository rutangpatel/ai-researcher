import os
from langgraph.store.mongodb import MongoDBStore
from langgraph.checkpoint.memory import InMemorySaver
from graph import graph
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
checkpoint = InMemorySaver()

def run_research(question: str):
    with MongoDBStore.from_conn_string(
        conn_string = MONGODB_URI,
        db_name = "ai-researcher",
        collection_name = "history"
    ) as memory:
        app = graph.compile(checkpointer = checkpoint, store = memory)
        config = {"configurable": {"thread_id": "research-1"}}

        for chunk in app.stream(
            {"question": question},
              config = config,
              stream_mode = "updates"):
            yield chunk