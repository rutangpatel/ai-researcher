import os
from langgraph.config import get_store
from pymongo import MongoClient
import voyageai

mongo_client = MongoClient(os.environ.get("MONGODB_URI"))
vo = voyageai.Client(api_key = os.environ.get("VOYAGE_API_KEY"))

db = mongo_client["socrates"]
collection = db["history"]

def embedding(question):
    return vo.embed(question, model = "voyage-4-lite").embeddings[0]

RECALL_HINTS = (
    "previous", "earlier", "before", "last time", "discussed",
    "talked", "asked", "remember", "history", "so far",
)

def is_recall_question(question):
    q = question.lower()
    return any(hint in q for hint in RECALL_HINTS)

def recent_memories(limit = 3):
    results = collection.find(
        {},
        {"_id": 0, "question": 1, "answer": 1}
    ).sort("_id", -1).limit(limit)
 
    return [
        {"question": r["value"]["question"], "answer": r["value"]["answer"], "score": 1}
        for r in results
    ]

def read_memory(state):
    query_embedding = embedding(state["question"])
    pipeline = [
        {
            "$vectorSearch":{
                "index": "vector_index",
                "path": "value.embedding",
                "queryVector": query_embedding,
                "numCandidates": 10,
                "limit": 5
            },
        },
        {
            "$project": {
                "_id": 0,
                "question": "$value.question",
                "answer": "$value.answer",
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    results = [
        result
        for result in results
        if result["score"] >= 0.65
    ]

    if not results and is_recall_question(state["question"]):
        results = recent_memories()

    return {"memory_context": results}