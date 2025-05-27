"""Example: Creating custom MCP tools for Synapse"""
from fastmcp import FastMCP
import httpx
import subprocess
from datetime import datetime

# Create MCP server
mcp = FastMCP("synapse-tools")


@mcp.tool()
async def web_search(query: str) -> str:
    """Search the web for information"""
    # Example using DuckDuckGo (no API key needed)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                return f"Summary: {abstract}"
            else:
                return "No summary found. Try a more specific query."
        else:
            return f"Search failed with status {response.status_code}"


@mcp.tool()
async def run_sql_query(query: str, database: str = "main") -> dict:
    """Execute a read-only SQL query
    
    Args:
        query: SQL query to execute (SELECT only)
        database: Database name (default: main)
    
    Returns:
        Query results as dict
    """
    # Validate query is read-only
    if not query.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed"}
    
    # TODO: Implement actual database connection
    # This is just an example structure
    return {
        "columns": ["id", "name", "created_at"],
        "rows": [
            [1, "Example", "2024-01-01"],
            [2, "Demo", "2024-01-02"]
        ],
        "row_count": 2
    }


@mcp.tool()
async def get_system_info() -> dict:
    """Get current system information"""
    import platform
    import psutil
    
    return {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total // (1024**3),  # GB
            "available": psutil.virtual_memory().available // (1024**3),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total // (1024**3),
            "free": psutil.disk_usage('/').free // (1024**3),
            "percent": psutil.disk_usage('/').percent
        }
    }


@mcp.tool()
async def execute_code(code: str, language: str = "python") -> str:
    """Execute code in a sandboxed environment
    
    Args:
        code: Code to execute
        language: Programming language (python, javascript, bash)
    
    Returns:
        Output from code execution
    """
    # WARNING: This is just an example. In production, use proper sandboxing!
    
    if language == "python":
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                
                # Execute with timeout
                result = subprocess.run(
                    ["python", f.name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                return f"Output:\n{result.stdout}\n\nErrors:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Code execution timed out (5 second limit)"
        except Exception as e:
            return f"Execution failed: {str(e)}"
    
    else:
        return f"Language '{language}' not supported. Use: python"


@mcp.tool()
async def create_reminder(
    message: str, 
    time: str,
    user_id: str = "default"
) -> dict:
    """Create a reminder for the user
    
    Args:
        message: Reminder message
        time: When to remind (e.g., "in 5 minutes", "tomorrow at 9am")
        user_id: User ID for the reminder
    
    Returns:
        Confirmation of reminder creation
    """
    # TODO: Implement actual reminder system
    # This would integrate with your notification system
    
    return {
        "status": "created",
        "reminder": {
            "message": message,
            "time": time,
            "user_id": user_id,
            "id": "reminder_123"
        }
    }


# To integrate with Synapse:
# 1. Save this file
# 2. Register the MCP server with Synapse
# 3. The tools will be available to the AI

if __name__ == "__main__":
    # Test the tools locally
    import asyncio
    
    async def test():
        result = await web_search("Python FastAPI")
        print("Search result:", result)
        
        info = await get_system_info()
        print("\nSystem info:", info)
    
    asyncio.run(test())