from graph import graph
from dotenv import load_dotenv
load_dotenv()

question = input("What is bugging you?\n\nYour question: ")
config = {"configurable": {"thread_id": "1"}}

result = graph.invoke({
    "question": question
}, config = config)

print("Response: ")
print(result["summary"])