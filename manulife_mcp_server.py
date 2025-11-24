from fastmcp import FastMCP
import os
from datetime import datetime
import snowflake.connector
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
load_dotenv()

# Create MCP server instance
mcp = FastMCP("Manulife Demo")

# Snowflake connection cache
_snowflake_conn = None

def get_snowflake_connection():
    """Get or create Snowflake connection using environment variables."""
    global _snowflake_conn
    
    if _snowflake_conn is not None:
        try:
            # Test if connection is still alive
            _snowflake_conn.cursor().execute("SELECT 1")
            return _snowflake_conn
        except:
            _snowflake_conn = None
    
    # Get credentials from environment variables
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    role = os.getenv("SNOWFLAKE_ROLE")
    
    if not all([account, user, password]):
        raise ValueError(
            "Missing required Snowflake credentials. Please set: "
            "SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD in .env file"
        )
    
    # Create connection
    conn_params = {
        "account": account,
        "user": user,
        "password": password,
        "warehouse": warehouse,
    }
    
    if database:
        conn_params["database"] = database
    if schema:
        conn_params["schema"] = schema
    if role:
        conn_params["role"] = role
    
    _snowflake_conn = snowflake.connector.connect(**conn_params)
    return _snowflake_conn



@mcp.tool()
def read_file(file_path: str = "sample.txt") -> str:
    """Read and return the contents of a file from the data directory."""
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

@mcp.tool()
def snowflake_query(sql: str, limit: Optional[int] = 100) -> Dict[str, Any]:
    """
    Execute a SQL query on Snowflake and return results.
    
    Args:
        sql: SQL query to execute (SELECT statements only for safety)
        limit: Maximum number of rows to return (default: 100, max: 1000)
    
    Returns:
        Dictionary containing columns, rows, and row_count
    """
    try:
        # Validate limit
        if limit and limit > 1000:
            limit = 1000
        
        # Get connection
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # For safety, only allow SELECT statements
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {
                "error": "Only SELECT queries are allowed for safety",
                "sql": sql
            }
        
        # Add LIMIT if not present
        if "LIMIT" not in sql_upper and limit:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        # Execute query
        cursor.execute(sql)
        
        # Fetch results
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to list of dicts for easier consumption
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        
        return {
            "success": True,
            "sql": sql,
            "columns": columns,
            "row_count": len(results),
            "rows": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sql": sql
        }

@mcp.tool()
def snowflake_show_tables(database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, Any]:
    """
    List all tables in Snowflake database/schema.
    
    Args:
        database: Database name (optional, uses connection default)
        schema: Schema name (optional, uses connection default)
    
    Returns:
        List of tables with their details
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Build SHOW TABLES query
        query = "SHOW TABLES"
        if database and schema:
            query += f" IN {database}.{schema}"
        elif database:
            query += f" IN DATABASE {database}"
        elif schema:
            query += f" IN SCHEMA {schema}"
        
        cursor.execute(query)
        
        # Fetch results
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        tables = []
        for row in rows:
            tables.append(dict(zip(columns, row)))
        
        cursor.close()
        
        return {
            "success": True,
            "table_count": len(tables),
            "tables": tables
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def snowflake_describe_table(table_name: str, database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the structure/schema of a Snowflake table.
    
    Args:
        table_name: Name of the table
        database: Database name (optional)
        schema: Schema name (optional)
    
    Returns:
        Table column definitions
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Build full table name
        full_table_name = table_name
        if database and schema:
            full_table_name = f"{database}.{schema}.{table_name}"
        elif schema:
            full_table_name = f"{schema}.{table_name}"
        
        query = f"DESCRIBE TABLE {full_table_name}"
        cursor.execute(query)
        
        # Fetch results
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        column_info = []
        for row in rows:
            column_info.append(dict(zip(columns, row)))
        
        cursor.close()
        
        return {
            "success": True,
            "table": full_table_name,
            "column_count": len(column_info),
            "columns": column_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table": table_name
        }

"""It is currently 2025-11-24 04:34 UTC, You are an analyst serving employees at an investment company. You may expect a prompt that may implicitly requesting sql query, or the task underlying the prompt may require information from the table. If this is the case, execute one or multiple queries with the following steps:
1. Make sure you know the names of database and scehema, if not, call suitable tool
2. Make sure you knows what table are exist, if not call suitable tools
3. execute correct sql querry to retrive data from table(s) and show the result and respective analysis
Now, Describe the BTCUSDT price movement in the past hour"""

"""
It is currently 2025-11-24 04:34 UTC, You are a data analyst. When a user asks about data: 1. ALWAYS call snowflake_show_tables if you don't know the tables 2. ALWAYS call snowflake_describe_table to see column names 3. ALWAYS call snowflake_query to execute SQL and get results 4. NEVER just write SQL - you MUST execute it using the tool Example: User: "Show me BTC prices" You MUST: - Call snowflake_query tool with the SQL - Show the actual results - Never stop at just writing SQL. Now, Describe the BTCUSDT price movement in the past hour
"""

'''@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    return a + b

@mcp.tool()
def reverse_string(text: str) -> str:
    return text[::-1]

@mcp.tool()
def get_random_joke() -> str:
    import random
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why do Java developers wear glasses? Because they can't C#!",
        "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?'"
    ]
    return random.choice(jokes)

@mcp.tool()
def calculate_bmi(weight: float, height: float) -> dict:
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
        }'''