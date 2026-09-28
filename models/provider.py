import os
from dotenv import load_dotenv

load_dotenv()

def get_chat_model():
    model = None
    smaller_model = None
    model_provider = os.getenv("MODEL_PROVIDER")

    if model_provider == "openai":
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model = os.getenv("OPENAI_MODEL"))
        smaller_model = ChatOpenAI(model = os.getenv("OPENAI_SMALLER_MODEL"))

    elif model_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = ChatGoogleGenerativeAI(model = os.getenv("GEMINI_MODEL"))
        smaller_model = ChatGoogleGenerativeAI(model = os.getenv("GEMINI_SMALLER_MODEL"))

    elif model_provider == "groq":
        from langchain_groq import ChatGroq
        model = ChatGroq(model = os.getenv("GROQ_MODEL"), reasoning_format = "hidden")
        smaller_model = ChatGroq(model = os.getenv("GROQ_SMALLER_MODEL"), reasoning_format = "hidden")

    if model == None or smaller_model == None:
        print("Provide proper API Key from provider like OpenAPI, Google or Groq")
        return

    return model, smaller_model