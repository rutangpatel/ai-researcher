import os
from langgraph.store.mongodb import MongoDBStore
from graph import graph, checkpoint
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]

with MongoDBStore.from_conn_string(
    conn_string = MONGODB_URI,
    db_name = "ai-researcher",
    collection_name = "history"
) as memory:
    app = graph.compile(checkpointer = checkpoint, store = memory)
    question = input("What is bugging you?\n\nYour question: ")
    config = {"configurable": {"thread_id": "research-1"}}

    result = app.invoke({
        "question": question
    }, config = config)

    print("Response: ")
    print(result["summary"])