# MCP Server with Snowflake Integration

This MCP (Model Context Protocol) server includes Snowflake database connectivity, allowing AI assistants to query and interact with your Snowflake data warehouse.

## 🎯 Features

### Original Tools
- `add_numbers` - Basic arithmetic
- `reverse_string` - String manipulation
- `get_random_joke` - Programming jokes
- `calculate_bmi` - Health calculations
- `get_weather` - Mock weather data
- `read_file` / `write_file` - File operations

### ❄️ New Snowflake Tools
- `snowflake_query` - Execute SQL SELECT queries on Snowflake
- `snowflake_show_tables` - List all tables in database/schema
- `snowflake_describe_table` - Get table structure and column information

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `fastmcp` - MCP server framework
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management
- `snowflake-connector-python` - Snowflake database connector

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-...

# Snowflake Credentials (REQUIRED)
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password

# Snowflake Optional Settings
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=your_role
```

#### Finding Your Snowflake Account Identifier

Your Snowflake account identifier can be found in your Snowflake URL:
- Format: `https://<account_identifier>.snowflakecomputing.com`
- Example: If your URL is `https://xy12345.us-east-1.snowflakecomputing.com`
- Then: `SNOWFLAKE_ACCOUNT=xy12345.us-east-1`

For newer account formats:
- Format: `https://<orgname>-<accountname>.snowflakecomputing.com`
- Example: `SNOWFLAKE_ACCOUNT=myorg-myaccount`

### 3. Test Snowflake Connection

Before running the full application, you can test your Snowflake connection:

```python
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
)

cursor = conn.cursor()
cursor.execute("SELECT CURRENT_VERSION()")
print(f"Connected! Snowflake version: {cursor.fetchone()[0]}")
cursor.close()
conn.close()
```

### 4. Run the Application

```bash
python raw_mcp_client.py
```

## 📖 Usage Examples

Once the application is running, you can ask questions like:

### Snowflake Queries

**List all tables:**
```
You: Show me all tables in my Snowflake database
```

**Describe a table:**
```
You: What are the columns in the CUSTOMERS table?
```

**Query data:**
```
You: Get the top 10 customers by revenue from the SALES table
```

**Complex queries:**
```
You: Run this query: SELECT customer_name, SUM(amount) as total FROM orders GROUP BY customer_name ORDER BY total DESC
```

### Combined Tool Usage

The AI can combine Snowflake tools with other tools:

```
You: Query the sales data from Snowflake and save the results to a file
```

```
You: Get weather data for Toronto and calculate the BMI for someone 1.75m tall weighing 75kg
```

## 🛠️ Snowflake Tool Details

### `snowflake_query`

Execute SELECT queries against Snowflake.

**Parameters:**
- `sql` (string, required): SQL SELECT query to execute
- `limit` (integer, optional): Maximum rows to return (default: 100, max: 1000)

**Returns:**
```json
{
  "success": true,
  "sql": "SELECT * FROM customers LIMIT 10",
  "columns": ["id", "name", "email"],
  "row_count": 10,
  "rows": [
    {"id": 1, "name": "John Doe", "email": "john@example.com"},
    ...
  ]
}
```

**Safety Features:**
- Only SELECT queries allowed (no INSERT, UPDATE, DELETE)
- Automatic LIMIT applied if not specified
- Maximum 1000 rows per query

### `snowflake_show_tables`

List tables in your Snowflake database.

**Parameters:**
- `database` (string, optional): Database name
- `schema` (string, optional): Schema name

**Returns:**
```json
{
  "success": true,
  "table_count": 5,
  "tables": [
    {
      "name": "CUSTOMERS",
      "database_name": "PROD_DB",
      "schema_name": "PUBLIC",
      ...
    }
  ]
}
```

### `snowflake_describe_table`

Get the structure of a specific table.

**Parameters:**
- `table_name` (string, required): Name of the table
- `database` (string, optional): Database name
- `schema` (string, optional): Schema name

**Returns:**
```json
{
  "success": true,
  "table": "CUSTOMERS",
  "column_count": 5,
  "columns": [
    {
      "name": "ID",
      "type": "NUMBER(38,0)",
      "kind": "COLUMN",
      "null?": "N",
      ...
    }
  ]
}
```

## 🔒 Security Notes

1. **Environment Variables**: Never commit your `.env` file to version control
2. **Read-Only Queries**: The `snowflake_query` tool only allows SELECT statements
3. **Row Limits**: Maximum 1000 rows per query to prevent overwhelming responses
4. **Connection Pooling**: Connection is cached and reused for efficiency

## 🐛 Troubleshooting

### "Missing required Snowflake credentials"

Make sure your `.env` file has the required fields:
- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`

### "Failed to connect to DB"

Check your account identifier format. Try both formats:
- Legacy: `xy12345.us-east-1`
- New: `myorg-myaccount`

### "Object does not exist"

Make sure you specify the correct database and schema, or set defaults in your `.env` file.

### Network/Firewall Issues

Ensure your network allows connections to Snowflake. Check:
- Snowflake account is not restricted by IP whitelisting
- Corporate firewall allows outbound HTTPS connections
- VPN is connected if required

## 📝 Example Session

```
🚀 MCP + OpenAI Integration (Raw JSON-RPC)

🔌 Connecting to MCP server: manulife_mcp_server.py
📡 Initializing...
✅ Initialized!
🔍 Discovering tools...
✅ Connected! Found 11 tools:
   • add_numbers
   • reverse_string
   • get_random_joke
   • calculate_bmi
   • get_weather
   • read_file
   • write_file
   • snowflake_query
   • snowflake_show_tables
   • snowflake_describe_table

💬 Chat (type 'quit' to exit)

You: Show me all tables in my database

🔧 Tool calls:
   • snowflake_show_tables({})

🤖 Assistant: I found 3 tables in your database:
1. CUSTOMERS - Customer information
2. ORDERS - Order transactions
3. PRODUCTS - Product catalog

You: What columns are in the CUSTOMERS table?

🔧 Tool calls:
   • snowflake_describe_table({"table_name": "CUSTOMERS"})

🤖 Assistant: The CUSTOMERS table has 5 columns:
- ID (NUMBER) - Primary key
- NAME (VARCHAR)
- EMAIL (VARCHAR)
- CREATED_DATE (DATE)
- STATUS (VARCHAR)
```

## 🎓 Next Steps

1. **Add More Snowflake Tools**: Extend with warehouse management, query history, etc.
2. **Error Handling**: Add retry logic and better error messages
3. **Caching**: Implement query result caching for frequently accessed data
4. **Monitoring**: Add logging and performance tracking
5. **Authentication**: Support for key-pair authentication and SSO

## 📚 Resources

- [Snowflake Python Connector Documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
