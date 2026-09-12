from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
load_dotenv()

# Structured Output format
class PlannerQuestions(BaseModel):
    question: List[str] = Field(description = "Sub-Question related to question")


planning_model = ChatOpenAI(model = "gpt-5.1").with_structured_output(PlannerQuestions)




