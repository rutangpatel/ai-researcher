import os
from dotenv import load_dotenv
from langchain_typesafe import TypeSafeClassifier
load_dotenv()

router = TypeSafeClassifier(api_key = os.getenv("TYPESAFE_API_KEY"))