# test_mcp_server.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_connection():
    """Test if we can connect to the MCP server"""
    try:
        print("🔌 Testing MCP server connection...")
        
        server_params = StdioServerParameters(
            command="python",
            args=["simple_mcp.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                init_result = await session.initialize()
                print("✅ MCP Server initialized:", init_result)
                
                # List available tools
                tools_result = await session.list_tools()
                print(f"📋 Found {len(tools_result.tools)} tools:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test a tool call
                print("\n🧪 Testing add_numbers tool...")
                result = await session.call_tool("add_numbers", {"a": 5, "b": 3})
                print(f"  Result: {result.content}")
                
                return True
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_connection())
    if result:
        print("\n🎉 MCP server connection successful!")
    else:
        print("\n💥 MCP server connection failed!")