from langchain.tools import tool
from langchain_tavily import TavilySearch

@tool
def web_search(query: str)-> str: 
    """Search the web for any information.
        Input:
        query: str

        Output:
        response: str
    """
    search = TavilySearch(
        max_results = 8,
        topic = "general",
        time_range = "week"
    )

    response = search.invoke({"query": query})
    return response
