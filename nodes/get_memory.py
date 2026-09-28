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

def read_memory(state):
    query_embedding = embedding(state["question"])
    pipeline = [
        {
            "$vectorSearch":{
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 10,
                "limit": 5
            },
        },
        {
            "$project": {
                "question": 1,
                "answer": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = collection.aggregate(pipeline)
    return results