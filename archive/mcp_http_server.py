# mcp_http_server.py - HTTP wrapper for MCP tools
from flask import Flask, request, jsonify
from manulife_mcp_server import (
    add_numbers, reverse_string, get_random_joke, 
    calculate_bmi, get_weather, read_file, write_file
)
import threading

app = Flask(__name__)

# Available tools
TOOLS = {
    "add_numbers": {
        "function": add_numbers,
        "description": "Add two numbers together",
        "parameters": ["a", "b"]
    },
    "reverse_string": {
        "function": reverse_string,
        "description": "Reverse a string", 
        "parameters": ["text"]
    },
    "get_random_joke": {
        "function": get_random_joke,
        "description": "Get a random programming joke",
        "parameters": []
    },
    "calculate_bmi": {
        "function": calculate_bmi,
        "description": "Calculate BMI and provide classification",
        "parameters": ["weight", "height"]
    },
    "get_weather": {
        "function": get_weather,
        "description": "Get current weather for a city",
        "parameters": ["city"]
    },
    "read_file": {
        "function": read_file,
        "description": "Read and return the contents of a file from the data directory",
        "parameters": ["file_path"]
    },
    "write_file": {
        "function": write_file,
        "description": "Write content to a file in the data directory",
        "parameters": ["content", "file_path"]
    }
}

@app.route('/tools', methods=['GET'])
def list_tools():
    """List all available tools"""
    tools_list = []
    for name, info in TOOLS.items():
        tools_list.append({
            "name": name,
            "description": info["description"],
            "parameters": info["parameters"]
        })
    return jsonify({"tools": tools_list})

@app.route('/tools/<tool_name>', methods=['POST'])
def call_tool(tool_name):
    """Call a specific tool"""
    if tool_name not in TOOLS:
        return jsonify({"error": f"Tool {tool_name} not found"}), 404
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        tool_info = TOOLS[tool_name]
        function = tool_info["function"]
        
        # Call the function with the provided arguments
        result = function(**data)
        
        return jsonify({"result": result})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "tools_available": len(TOOLS)})

if __name__ == '__main__':
    print("🚀 Starting HTTP MCP Server on port 8000...")
    print("📋 Available tools:", ", ".join(TOOLS.keys()))
    app.run(host='0.0.0.0', port=8000, debug=False)