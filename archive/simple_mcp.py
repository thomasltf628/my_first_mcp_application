from fastmcp import FastMCP
import requests
import os
import json
from datetime import datetime

# Create MCP server instance
mcp = FastMCP("Manulife Demo")

@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    print(f"[MCP Server] add_numbers called with a={a}, b={b}")
    return a + b

@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse a string."""
    print(f"[MCP Server] reverse_string called with text='{text}'")
    return text[::-1]

@mcp.tool()
def get_random_joke() -> str:
    """Get a random programming joke."""
    print(f"[MCP Server] get_random_joke called")
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why do Java developers wear glasses? Because they can't C#!",
        "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?'"
    ]
    import random
    return random.choice(jokes)

@mcp.tool()
def calculate_bmi(weight: float, height: float) -> dict:
    """Calculate BMI and provide classification."""
    print(f"[MCP Server] calculate_bmi called with weight={weight}, height={height}")
    bmi = weight / (height ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return {"bmi": round(bmi, 2), "category": category}

@mcp.tool()
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    print(f"[MCP Server] get_weather called with city='{city}'")
    try:
        # Mock weather data
        weather_data = {
            "toronto": {"temperature": 22, "condition": "Sunny", "humidity": 65},
            "london": {"temperature": 15, "condition": "Cloudy", "humidity": 80},
            "tokyo": {"temperature": 28, "condition": "Rainy", "humidity": 75},
            "new york": {"temperature": 20, "condition": "Partly Cloudy", "humidity": 70}
        }
        
        city_lower = city.lower()
        if city_lower in weather_data:
            return {
                "city": city,
                **weather_data[city_lower],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "city": city,
                "temperature": 20,
                "condition": "Unknown",
                "humidity": 50,
                "note": "Mock data - city not in database"
            }
    except Exception as e:
        return {"error": f"Failed to get weather: {str(e)}"}

@mcp.tool()
def read_file(file_path: str = "sample.txt") -> str:
    """Read and return the contents of a file from the data directory."""
    print(f"[MCP Server] read_file called with file_path='{file_path}'")
    try:
        data_dir = "data"
        full_path = os.path.join(data_dir, file_path)
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            return f"Data directory created. Please add files to {data_dir}/"
        
        if not os.path.exists(full_path):
            sample_content = f"Sample file created at {datetime.now()}\nFile: {file_path}"
            with open(full_path, 'w') as f:
                f.write(sample_content)
            return f"Created sample file. Content:\n{sample_content}"
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        return f"File: {file_path}\nContent:\n{content}"
        
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(content: str, file_path: str = "sample.txt") -> str:
    """Write content to a file in the data directory."""
    print(f"[MCP Server] write_file called with file_path='{file_path}'")
    try:
        data_dir = "data"
        full_path = os.path.join(data_dir, file_path)
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        return f"Successfully wrote to {file_path}"
        
    except Exception as e:
        return f"Error writing file: {str(e)}"

if __name__ == "__main__":
    print("🚀 Starting Manulife MCP Server...")
    print("Available tools:")
    print("- add_numbers(a, b)")
    print("- reverse_string(text)")
    print("- get_random_joke()")
    print("- calculate_bmi(weight, height)")
    print("- get_weather(city)")
    print("- read_file(file_path)")
    print("- write_file(content, file_path)")
    print("Server is running and waiting for connections...")
    mcp.run()