from pydantic import BaseModel, Field
from typing import List
from models.provider import get_chat_model

# Structured Output format
class PlannerQuestions(BaseModel):
    question: List[str] = Field(description = "Sub-Question related to question")

planning_model = get_chat_model().with_structured_output(PlannerQuestions)