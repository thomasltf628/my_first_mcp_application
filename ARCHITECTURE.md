# 🏗️ Architecture Diagram

## System Flow: User → AI → Snowflake

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INPUT                             │
│  "Show me top 5 customers by revenue from Snowflake"           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   raw_mcp_client.py                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 1. Receives user input                                     │ │
│  │ 2. Calls OpenAI API with all available MCP tools          │ │
│  │ 3. OpenAI decides which tool(s) to use                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ JSON-RPC Request
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              manulife_mcp_server.py (MCP Server)                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Available Tools (11 total)                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Original Tools (8):                                      │  │
│  │   • add_numbers                                           │  │
│  │   • reverse_string                                        │  │
│  │   • get_random_joke                                       │  │
│  │   • calculate_bmi                                         │  │
│  │   • get_weather                                           │  │
│  │   • read_file                                             │  │
│  │   • write_file                                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ❄️  NEW Snowflake Tools (3):                            │  │
│  │   • snowflake_query          ← Execute SQL               │  │
│  │   • snowflake_show_tables    ← List tables              │  │
│  │   • snowflake_describe_table ← Get table schema         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Snowflake Connection Manager                      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ get_snowflake_connection()                         │  │  │
│  │  │ • Reads .env credentials                           │  │  │
│  │  │ • Creates/caches connection                        │  │  │
│  │  │ • Validates connection is alive                    │  │  │
│  │  │ • Auto-reconnects if needed                        │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ SQL Query
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SNOWFLAKE DATA WAREHOUSE                     │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   CUSTOMERS    │  │     ORDERS     │  │   PRODUCTS     │   │
│  │   Table        │  │     Table      │  │     Table      │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                 │
│  Authentication via:                                            │
│   • Account: your_account.region                               │
│   • User: your_username                                        │
│   • Password: your_password (from .env)                        │
│   • Warehouse: COMPUTE_WH                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Query Results
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Results Flow (Back to User)                        │
│                                                                 │
│  Snowflake → MCP Server → MCP Client → OpenAI → User           │
│                                                                 │
│  Format: JSON with columns, rows, metadata                     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface (Terminal/CLI)
- User types natural language queries
- Receives formatted AI responses
- Can ask follow-up questions

### 2. MCP Client (raw_mcp_client.py)
**Responsibilities:**
- Manages conversation with user
- Communicates with OpenAI API
- Sends JSON-RPC requests to MCP server
- Formats responses for user

**Key Functions:**
- `chat()` - Main conversation loop
- `call_tool()` - Execute MCP tools
- `get_openai_tools()` - Convert MCP tools to OpenAI format

### 3. MCP Server (manulife_mcp_server.py)
**Responsibilities:**
- Hosts all available tools
- Manages Snowflake connection
- Executes queries and operations
- Returns structured results

**Key Components:**
- Tool definitions (@mcp.tool() decorators)
- Connection manager function
- Query execution logic
- Error handling

### 4. Snowflake Connection Layer
**Authentication Flow:**
```
.env file → get_snowflake_connection() → snowflake.connector.connect()
```

**Credentials Required:**
- SNOWFLAKE_ACCOUNT
- SNOWFLAKE_USER  
- SNOWFLAKE_PASSWORD
- (Optional: WAREHOUSE, DATABASE, SCHEMA, ROLE)

**Connection Features:**
- Singleton pattern (one connection cached)
- Lazy initialization (connects on first use)
- Health checks (validates before each query)
- Auto-reconnection (if connection drops)

### 5. Snowflake Data Warehouse
**What It Provides:**
- Data storage and management
- SQL query processing
- Scalable compute resources
- Secure access control

## Data Flow Example

Let's trace a complete request:

**User:** "What are the top 3 customers?"

**Step 1:** raw_mcp_client.py receives input
```python
user_input = "What are the top 3 customers?"
```

**Step 2:** Client calls OpenAI with all tools
```python
response = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": user_input}],
    tools=all_mcp_tools  # Including snowflake_query
)
```

**Step 3:** OpenAI decides to use snowflake_query
```json
{
  "tool": "snowflake_query",
  "arguments": {
    "sql": "SELECT customer_name, total_revenue FROM customers ORDER BY total_revenue DESC LIMIT 3"
  }
}
```

**Step 4:** Client sends JSON-RPC to MCP server
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "snowflake_query",
    "arguments": { "sql": "..." }
  }
}
```

**Step 5:** MCP server calls get_snowflake_connection()
- Checks if cached connection exists
- Validates connection is alive
- Returns connection object

**Step 6:** Server executes query on Snowflake
```python
cursor.execute(sql)
rows = cursor.fetchall()
```

**Step 7:** Snowflake returns results
```
[
  ("Acme Corp", 1245000),
  ("Global Industries", 987500),
  ("Tech Solutions", 856000)
]
```

**Step 8:** Server formats and returns to client
```json
{
  "success": true,
  "columns": ["customer_name", "total_revenue"],
  "rows": [
    {"customer_name": "Acme Corp", "total_revenue": 1245000},
    {"customer_name": "Global Industries", "total_revenue": 987500},
    {"customer_name": "Tech Solutions", "total_revenue": 856000}
  ],
  "row_count": 3
}
```

**Step 9:** Client sends results to OpenAI

**Step 10:** OpenAI generates natural language response
```
"Here are your top 3 customers by revenue:

1. Acme Corp - $1,245,000
2. Global Industries - $987,500
3. Tech Solutions - $856,000"
```

**Step 11:** User sees final response

## Security Layers

```
┌─────────────────────────────────────────────┐
│         Environment Variables (.env)        │
│  • Credentials stored locally only          │
│  • Never committed to version control       │
│  • Loaded at runtime                        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│          Connection Manager                  │
│  • Validates credentials exist              │
│  • Establishes encrypted connection         │
│  • Manages authentication                   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│          Query Safety Layer                  │
│  • Only SELECT queries allowed              │
│  • Row limits enforced (max 1000)          │
│  • SQL injection prevention                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│          Snowflake Security                  │
│  • User permissions and roles               │
│  • Database access control                  │
│  • Audit logging                            │
└─────────────────────────────────────────────┘
```

## File Dependencies

```
.env
 ├─→ manulife_mcp_server.py (reads credentials)
 └─→ test_snowflake.py (reads credentials)

requirements.txt
 └─→ All Python dependencies

manulife_mcp_server.py
 └─→ Imported by: fastmcp run command

raw_mcp_client.py
 ├─→ Imports: openai, asyncio, json
 └─→ Starts: manulife_mcp_server.py as subprocess
```

## Quick Reference: What Each File Does

| File | Purpose |
|------|---------|
| **manulife_mcp_server.py** | MCP server with 11 tools (8 original + 3 Snowflake) |
| **raw_mcp_client.py** | Client that connects user ↔ OpenAI ↔ MCP server |
| **requirements.txt** | Python dependencies list |
| **.env** | Credentials (you create this from env.example) |
| **env.example** | Template for .env file |
| **test_snowflake.py** | Standalone connection tester |
| **README.md** | Complete documentation |
| **QUICKSTART.md** | 5-minute setup guide |
| **SUMMARY.md** | Overview of changes made |

---

This architecture ensures:
✅ Secure credential management
✅ Efficient connection pooling  
✅ Safe query execution
✅ Natural language interface
✅ Extensibility for future tools
