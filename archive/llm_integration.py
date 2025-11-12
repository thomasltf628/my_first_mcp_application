import os
import asyncio
import json
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
load_dotenv()

class MCPOpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = OpenAI(api_key=self.api_key)
        self.available_tools = []
    
    async def connect_to_mcp_server(self):
        """Connect to the MCP server and discover available tools"""
        try:
            server_params = StdioServerParameters(
                command="python",
                args=["simple_mcp.py"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    init_result = await session.initialize()
                    print("✅ Connected to MCP server")
                    
                    # List available tools from the server
                    tools_result = await session.list_tools()
                    self.available_tools = tools_result.tools
                    
                    print(f"📋 Discovered {len(self.available_tools)} tools from MCP server:")
                    for tool in self.available_tools:
                        print(f"  - {tool.name}: {tool.description}")
                    
                    return session
                    
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            raise
    
    def convert_mcp_tools_to_openai_format(self):
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        
        for tool in self.available_tools:
            # Convert MCP tool to OpenAI function format
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Tool: {tool.name}",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add input schema if available
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                openai_tool["function"]["parameters"] = tool.inputSchema
            elif tool.inputSchema:
                openai_tool["function"]["parameters"] = tool.inputSchema
            
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def chat_with_tools(self, session: ClientSession, user_message: str):
        """Chat with OpenAI using tools discovered from MCP server"""
        if not self.available_tools:
            return "No tools available from MCP server"
        
        # Convert MCP tools to OpenAI format
        openai_tools = self.convert_mcp_tools_to_openai_format()
        
        try:
            # First, ask OpenAI what tools to use
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_message}],
                tools=openai_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                print("🔧 Tool calls requested by OpenAI:")
                tool_results = []
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"  - Calling {function_name} with args: {function_args}")
                    
                    # Call the tool through MCP server
                    try:
                        result = await session.call_tool(function_name, function_args)
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "result": result.content
                        })
                        print(f"  ✅ Result: {result.content}")
                    except Exception as e:
                        error_msg = f"Error calling {function_name}: {str(e)}"
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "result": error_msg
                        })
                        print(f"  ❌ {error_msg}")
                
                # Send results back to OpenAI
                second_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": user_message},
                        message,
                        *[
                            {
                                "role": "tool",
                                "tool_call_id": tr["tool_call_id"],
                                "content": str(tr["result"])
                            }
                            for tr in tool_results
                        ]
                    ]
                )
                
                return second_response.choices[0].message.content
            else:
                return message.content
                
        except Exception as e:
            return f"Error in chat_with_tools: {str(e)}"

async def main():
    """Main function to run the MCP-OpenAI integration"""
    print("🚀 Starting MCP-OpenAI Integration...")
    
    try:
        # Create client
        client = MCPOpenAIClient()
        
        # Connect to MCP server and discover tools
        print("🔌 Connecting to MCP server...")
        session = await client.connect_to_mcp_server()
        
        print("\n💬 Interactive Mode - Type 'quit' to exit")
        print("Available tools discovered automatically from MCP server!")
        
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye! 👋")
                break
                
            if user_input:
                try:
                    response = await client.chat_with_tools(session, user_input)
                    print(f"Assistant: {response}")
                except Exception as e:
                    print(f"Error: {e}")
                    
    except Exception as e:
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())