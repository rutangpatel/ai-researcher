from tools.search import web_search
from models.provider import get_chat_model

research_model, _ = get_chat_model()
research_model = research_model.bind_tools([web_search])