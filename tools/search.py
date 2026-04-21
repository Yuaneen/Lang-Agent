from langchain.tools import tool

@tool
def search(query: str) -> str:
    """Search the web for information."""

    
    return "I found some information for you: " + query