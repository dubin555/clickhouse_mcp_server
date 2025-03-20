import re
import logging

logger = logging.getLogger("clickhouse_mcp_server")

def dangerous_check(query: str) -> tuple[bool, str]:
    """
    Perform a security check on the query to prevent SQL injection attacks.
    This function checks for the presence of potentially dangerous keywords and patterns 
    that could be used to inject malicious code.

    Args:
        query (str): The SQL query to be checked.
    Returns:
        tuple[bool, str]: A tuple containing a boolean indicating whether the query is dangerous
                          and a string with the detected dangerous pattern, if any.
    """

    # List of dangerous keywords and patterns
    dangerous_keywords = [
        "insert", "update", "delete", "drop", "truncate", "alter" 
    ]

    # Check for dangerous keywords
    for keyword in dangerous_keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", query, re.IGNORECASE):
            logger.warning(f"Dangerous keyword '{keyword}' detected in query: {query}")
            return True, f"Query contains dangerous keyword '{keyword}'"
    return False, "Query is safe"