import os
from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()

# Import the functional tools from simple_mcp
try:
    from simple_mcp import add_numbers, reverse_string, get_random_joke, calculate_bmi
    USING_REAL_TOOLS = True
    print("Using real MCP tools from simple_mcp.py")
except ImportError as e:
    print(f"Could not import from simple_mcp.py: {e}")
    print("Using simulated tools instead")
    USING_REAL_TOOLS = False

class MCPOpenAIIntegration:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.client = OpenAI(api_key=self.api_key)
        self.using_real_tools = USING_REAL_TOOLS
    
    def call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call MCP tool with given arguments"""
        if self.using_real_tools:
            if tool_name == "add_numbers":
                return add_numbers(**arguments)
            elif tool_name == "reverse_string":
                return reverse_string(**arguments)
            elif tool_name == "get_random_joke":
                return get_random_joke()
            elif tool_name == "calculate_bmi":
                return calculate_bmi(**arguments)
            else:
                return f"Tool {tool_name} not found"
        else:
            # Use simulated tools as fallback
            print("Fallback")
            return self._call_simulated_tool(tool_name, arguments)
    
    def _call_simulated_tool(self, tool_name: str, arguments: dict):
        """Fallback simulated tools"""
        if tool_name == "add_numbers":
            a = arguments.get('a', 0)
            b = arguments.get('b', 0)
            return a + b
        elif tool_name == "reverse_string":
            text = arguments.get('text', '')
            return text[::-1]
        elif tool_name == "get_random_joke":
            return "Why do programmers prefer dark mode? Because light attracts bugs!"
        elif tool_name == "calculate_bmi":
            weight = arguments.get('weight', 0)
            height = arguments.get('height', 1)
            bmi = weight / (height ** 2)
            return f"BMI: {bmi:.2f}"
        else:
            return f"Tool {tool_name} not found"
    
    def chat_with_tools(self, user_message: str):
        """Chat with OpenAI using MCP tools"""
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_numbers",
                    "description": "Add two numbers together",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reverse_string",
                    "description": "Reverse a string",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Input string to reverse"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_random_joke",
                    "description": "Get a random programming joke",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_bmi",
                    "description": "Calculate BMI and provide classification",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "weight": {"type": "number", "description": "Weight in kilograms"},
                            "height": {"type": "number", "description": "Height in meters"}
                        },
                        "required": ["weight", "height"]
                    }
                }
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_message}],
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                print("🔧 OpenAI requested tool calls:")
                tool_results = []
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"  - Calling {function_name} with args: {function_args}")
                    
                    result = self.call_mcp_tool(function_name, function_args)
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "function_name": function_name,
                        "result": result
                    })
                
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
            return f"Error: {str(e)}"

if __name__ == "__main__":
    print("🚀 Testing MCP-OpenAI Integration...")
    
    integration = MCPOpenAIIntegration()
    
    if integration.using_real_tools:
        print("✅ Connected to real MCP tools from simple_mcp.py")
    else:
        print("⚠️ Using simulated tools (simple_mcp.py not available)")
    
    print("\n💬 Interactive Mode - Type 'quit' to exit")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye! 👋")
            break
            
        if user_input:
            try:
                response = integration.chat_with_tools(user_input)
                print(f"Assistant: {response}")
            except Exception as e:
                print(f"Error: {e}")