"""
Example client for the Legal MCP Server

This demonstrates how to connect to and use the Legal MCP server
from a Python client.
"""

import asyncio
from fastmcp import Client


async def main():
    """Example usage of the Legal MCP client"""
    
    # Connect to the server
    # Use stdio transport for local development
    # For HTTP: client = Client("http://localhost:8001/mcp")
    client = Client("stdio://server/main.py:mcp")
    
    async with client:
        print("🔍 Connected to Legal MCP Server\n")
        
        # List available resources
        print("📚 Available Resources:")
        resources = await client.list_resources()
        for resource in resources:
            print(f"  • {resource.uri}: {resource.name}")
        print()
        
        # Read the available codes resource
        print("📖 Reading available legal codes:")
        codes_content = await client.read_resource("legal://codes/available")
        print(codes_content[0].text)
        print()
        
        # List available tools
        print("🛠️  Available Tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")
        print()
        
        # Example: Search legal texts
        print("🔎 Example: Searching for 'Vertrag' in BGB:")
        result = await client.call_tool(
            "search_legal_texts",
            {
                "query": "Vertrag und Vereinbarung",
                "code": "bgb",
                "limit": 3,
                "cutoff": 0.5,
            },
        )
        print(result)
        print()
        
        # Example: Get specific section
        print("📄 Example: Getting BGB § 1:")
        result = await client.call_tool(
            "get_legal_section",
            {
                "code": "bgb",
                "section": "§ 1",
            },
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(main())

