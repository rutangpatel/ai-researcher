from tools.search import web_search
from models.provider import get_chat_model

research_model = get_chat_model().bind_tools([web_search])