import os
import asyncio
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class RawMCPClient:
    """MCP Client using raw JSON-RPC messages instead of ClientSession"""
    
    def __init__(self, server_script_name="manulife_mcp_server.py"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.openai_client = OpenAI(api_key=self.api_key)
        self.server_script = Path(server_script_name).resolve()
        self.process = None
        self.available_tools = []
        self.request_id = 0
    
    def _next_id(self):
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, method: str, params: dict = None):
        """Send a JSON-RPC request and get response"""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id(),
        }
        if params:
            request["params"] = params
        
        # Send request
        message = json.dumps(request) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
        
        # Read response, skipping any non-JSON lines (like banner output)
        max_attempts = 10
        for attempt in range(max_attempts):
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=10
            )
            
            if not response_line:
                raise RuntimeError("No response from server")
            
            line = response_line.decode().strip()
            
            # Skip empty lines or lines that don't look like JSON
            if not line or not line.startswith('{'):
                continue
            
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                # Not valid JSON, try next line
                continue
        
        raise RuntimeError("Could not find valid JSON response")
    
    async def connect(self):
        """Connect to MCP server"""
        if not self.server_script.exists():
            raise FileNotFoundError(f"Server script not found: {self.server_script}")
        
        print(f"🔌 Connecting to MCP server: {self.server_script.name}")
        
        # Start server process with environment to disable banner
        env = os.environ.copy()
        env["FASTMCP_NO_BANNER"] = "1" # Couldn't found on ENV variables list, don't know if it useful, keep anyway
        
        self.process = await asyncio.create_subprocess_exec(
            "fastmcp", "run", str(self.server_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(0.5)
        
        # Send initialize request
        print("📡 Initializing...")
        init_response = await self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05", # 2025-06-18 supported, save for recent compatibility
                "capabilities": {},
                "clientInfo": {
                    "name": "manulife-client",
                    "version": "1.0.0"
                }
            }
        )
        
        if "error" in init_response:
            raise RuntimeError(f"Initialize failed: {init_response['error']}")
        
        print("✅ Initialized!")
        
        # List tools
        print("🔍 Discovering tools...")
        tools_response = await self._send_request("tools/list")
        
        if "error" in tools_response:
            raise RuntimeError(f"List tools failed: {tools_response['error']}")
        
        # Parse tools
        self.available_tools = tools_response["result"]["tools"]
        
        print(f"✅ Connected! Found {len(self.available_tools)} tools:")
        for tool in self.available_tools:
            print(f"   • {tool['name']}")
        
        return True
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=2)
            except:
                self.process.kill()
    
    def get_openai_tools(self):
        """Convert MCP tools to OpenAI format"""
        openai_tools = []
        for tool in self.available_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", f"Execute {tool['name']}"),
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                }
            })
        return openai_tools
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call an MCP tool"""
        response = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        if "error" in response:
            raise RuntimeError(f"Tool call failed: {response['error']}")
        
        # Extract content from result
        result = response["result"]
        if "content" in result and len(result["content"]) > 0:
            return result["content"][0]["text"]
        return str(result)
    
    async def chat(self, user_message: str, model="gpt-3.5-turbo"):
        """Chat with OpenAI using MCP tools"""
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
            
            # Execute each tool call
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
        
        return message.content


async def main():
    print("🚀 MCP + OpenAI Integration (Raw JSON-RPC)\n")
    
    client = RawMCPClient()
    
    try:
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
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
