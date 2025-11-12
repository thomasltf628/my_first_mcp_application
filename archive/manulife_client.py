import os
import asyncio
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


class MCPClient:
    def __init__(self, server_script_name="manulife_mcp_server.py"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.openai_client = OpenAI(api_key=self.api_key)
        self.server_script = Path(server_script_name).resolve()
        self.session = None
        self.available_tools = []
        self.read_stream = None
        self.write_stream = None
        self.exit_stack = None
    
    async def connect(self):
        """Connect to MCP server and discover tools"""
        if not self.server_script.exists():
            raise FileNotFoundError(f"Server script not found: {self.server_script}")
        
        print(f"🔌 Connecting to MCP server: {self.server_script.name}")
        
        server_params = StdioServerParameters(
            command="fastmcp",
            args=["run", str(self.server_script)],
            env=None
        )
        
        try:
            # Use stdio_client properly as async context manager
            self.exit_stack = stdio_client(server_params)
            self.read_stream, self.write_stream = await self.exit_stack.__aenter__()
            
            # Create session
            self.session = ClientSession(self.read_stream, self.write_stream)
            
            # Initialize with timeout
            await asyncio.wait_for(self.session.initialize(), timeout=30)
            
            print('now find tools')
            # Discover tools
            tools_response = await asyncio.wait_for(
                self.session.list_tools(), 
                timeout=30
            )
            self.available_tools = tools_response.tools
            
            print(f"✅ Connected! Found {len(self.available_tools)} tools:")
            for tool in self.available_tools:
                print(f"   • {tool.name}")
            
            return True
            
        except asyncio.TimeoutError:
            await self._cleanup()
            raise TimeoutError(
                f"Connection timeout.\n"
                f"The server started but didn't respond in time."
            )
        except Exception as e:
            await self._cleanup()
            raise RuntimeError(f"Connection failed: {e}")
    
    async def _cleanup(self):
        """Internal cleanup without error propagation"""
        if self.exit_stack:
            try:
                await self.exit_stack.__aexit__(None, None, None)
            except:
                pass  # Suppress all cleanup errors
    
    async def disconnect(self):
        """Clean disconnect"""
        await self._cleanup()
    
    def get_openai_tools(self):
        """Convert MCP tools to OpenAI function format"""
        openai_tools = []
        for tool in self.available_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "parameters": tool.inputSchema
                }
            })
        return openai_tools
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call an MCP tool"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self.session.call_tool(tool_name, arguments)
        
        # Extract result
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return str(result)
    
    async def chat(self, user_message: str, model="gpt-3.5-turbo"):
        """Chat with OpenAI using MCP tools"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        openai_tools = self.get_openai_tools()
        
        # First OpenAI call
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_message}],
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # If OpenAI wants to call tools
        if message.tool_calls:
            print("\n🔧 Tool calls:")
            
            # Execute each tool call through MCP
            tool_results = []
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"   • {func_name}({json.dumps(func_args)})")
                
                # Call through MCP
                result = await self.call_tool(func_name, func_args)
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": str(result)
                })
            
            # Second OpenAI call with results
            final_response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": user_message},
                    message,
                    *tool_results
                ]
            )
            
            return final_response.choices[0].message.content
        
        # No tool calls needed
        return message.content


async def main():
    print("🚀 MCP + OpenAI Integration\n")
    
    client = MCPClient()
    
    try:
        # Connect
        await client.connect()
        
        print("\n💬 Chat (type 'quit' to exit)\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = await client.chat(user_input)
                print(f"\n🤖 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure manulife_mcp_server.py is in the same directory")
        print("  2. Test server: fastmcp dev manulife_mcp_server.py")
        print("  3. Check .env file has OPENAI_API_KEY")
    
    finally:
        # Clean disconnect
        await client.disconnect()
        
        # Give Windows time to clean up
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")