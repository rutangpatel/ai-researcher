from langchain_openai import ChatOpenAI
from tools.search import web_search

research_model = ChatOpenAI(model = "gpt-5.1").bind_tools([web_search])