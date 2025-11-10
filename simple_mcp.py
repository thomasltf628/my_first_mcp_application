from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("Simple Demo")

def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]

def get_random_joke() -> str:
    """Get a random programming joke."""
    return "Why do programmers prefer dark mode? Because light attracts bugs!"

def calculate_bmi(weight: float, height: float) -> dict:
    """Calculate BMI and provide classification."""
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

# Register functions as MCP tools
@mcp.tool()
def add_numbers_tool(a: float, b: float) -> float:
    return add_numbers(a, b)

@mcp.tool()
def reverse_string_tool(text: str) -> str:
    return reverse_string(text)

@mcp.tool()
def get_random_joke_tool() -> str:
    return get_random_joke()

@mcp.tool()
def calculate_bmi_tool(weight: float, height: float) -> dict:
    return calculate_bmi(weight, height)

__all__ = ['add_numbers', 'reverse_string', 'get_random_joke', 'calculate_bmi'] # Essetial for importing to llm_integration

if __name__ == "__main__":
    # Only run the server if executed directly
    mcp.run()