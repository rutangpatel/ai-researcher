from graph import graph
from dotenv import load_dotenv
load_dotenv()

question = input("What is bugging you?\n")

result = graph.invoke({
    "question": question
})

print("******************")
print("Response: \n")
print(result["summary"])