# mcp_http_client.py - Simple HTTP-based MCP client
import requests
import json
import time

class SimpleMCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tools = []
    
    def discover_tools(self):
        """Discover available tools from the MCP server"""
        try:
            response = requests.get(f"{self.base_url}/tools", timeout=10)
            if response.status_code == 200:
                self.tools = response.json().get('tools', [])
                print(f"📋 Discovered {len(self.tools)} tools:")
                for tool in self.tools:
                    print(f"  - {tool['name']}: {tool['description']}")
                return True
            else:
                print(f"❌ Failed to discover tools: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error discovering tools: {e}")
            return False
    
    def call_tool(self, tool_name, arguments):
        """Call a tool on the MCP server"""
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

# Test the client
if __name__ == "__main__":
    client = SimpleMCPClient()
    if client.discover_tools():
        # Test a tool call
        result = client.call_tool("add_numbers", {"a": 5, "b": 3})
        print(f"🧪 Test result: {result}")