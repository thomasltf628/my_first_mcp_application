# http_client.py - HTTP-based client (much more reliable on Windows)
import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class HTTPMCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.openai_client = OpenAI(api_key=self.api_key)
        self.tools = []
    
    def connect(self):
        """Connect to HTTP MCP server"""
        try:
            response = requests.get(f"{self.base_url}/tools", timeout=10)
            if response.status_code == 200:
                self.tools = response.json().get('tools', [])
                print(f"✅ Connected! Found {len(self.tools)} tools:")
                for tool in self.tools:
                    print(f"   • {tool['name']}: {tool['description']}")
                return True
            else:
                print(f"❌ Failed to connect: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("💡 Make sure mcp_http_server.py is running on port 8000")
            return False
    
    def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool via HTTP"""
        try:
            response = requests.post(
                f"{self.base_url}/tools/{tool_name}",
                json=arguments,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('result', 'No result')
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error calling tool: {str(e)}"
    
    def get_openai_tools(self):
        """Convert to OpenAI format"""
        openai_tools = []
        for tool in self.tools:
            # Build parameter schema
            properties = {}
            required = []
            
            for param in tool.get('parameters', []):
                # Simple type inference
                param_type = "string"
                if param in ['a', 'b', 'weight', 'height']:
                    param_type = "number"
                
                properties[param] = {"type": param_type}
                required.append(param)
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool['name'],
                    "description": tool['description'],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        return openai_tools
    
    def chat(self, user_message: str, model="gpt-3.5-turbo"):
        """Chat with OpenAI using HTTP tools"""
        if not self.tools:
            return "No tools available. Please connect first."
        
        openai_tools = self.get_openai_tools()
        
        # First OpenAI call
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_message}],
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            print("\n🔧 Tool calls:")
            tool_results = []
            
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                print(f"   • {func_name}({json.dumps(func_args)})")
                
                # Call via HTTP
                result = self.call_tool(func_name, func_args)
                print(f"     → {result}")
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool", 
                    "content": str(result)
                })
            
            # Second call with results
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

def main():
    print("🚀 HTTP MCP + OpenAI Integration (Windows Compatible)\n")
    
    client = HTTPMCPClient()
    
    if not client.connect():
        return
    
    print("\n💬 Chat (type 'quit' to exit)\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = client.chat(user_input)
            print(f"\n🤖 Assistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()