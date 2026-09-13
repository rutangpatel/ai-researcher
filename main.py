from graph import graph
from dotenv import load_dotenv
load_dotenv()

question = input("What is bugging you?\n")
config = {"configurable": {"thread_id": "3"}}

result = graph.invoke({
    "question": question
}, config = config)

print("******************")
print("Response: \n")
print(result["summary"])