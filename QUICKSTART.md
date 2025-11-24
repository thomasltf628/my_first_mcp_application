# 🚀 Quick Start Guide - Snowflake MCP Integration

## What I Added

I've added **3 Snowflake MCP tools** to your application:

1. **snowflake_query** - Execute SQL SELECT queries
2. **snowflake_show_tables** - List all tables in database/schema  
3. **snowflake_describe_table** - Get table structure/columns

These tools allow your AI assistant to query and explore Snowflake data!

## ⚡ Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
pip install snowflake-connector-python
```

(The other dependencies you already have: fastmcp, openai, python-dotenv)

### Step 2: Configure Snowflake Credentials

Create/edit your `.env` file and add:

```env
# Your existing OpenAI key
OPENAI_API_KEY=sk-your-key-here

# Add these Snowflake credentials:
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=your_database  # optional
SNOWFLAKE_SCHEMA=PUBLIC            # optional
```

**Finding your Snowflake Account:**
- Look at your Snowflake URL: `https://[THIS-PART].snowflakecomputing.com`
- Example: `https://xy12345.us-east-1.snowflakecomputing.com` → Use `xy12345.us-east-1`

### Step 3: Test Connection (Optional but Recommended)

```bash
python test_snowflake.py
```

This will verify your credentials work before running the full app.

### Step 4: Run Your Application

```bash
python raw_mcp_client.py
```

## 💡 Try These Commands

Once running, try asking:

```
You: Show me all tables in my Snowflake database
```

```
You: What are the columns in the CUSTOMERS table?
```

```
You: Query the top 10 rows from the SALES table
```

```
You: Run this SQL: SELECT customer_name, SUM(revenue) FROM orders GROUP BY customer_name LIMIT 5
```

## 🔧 How It Works

**Authentication:**
- Credentials are loaded from `.env` file
- Connection is created when first Snowflake tool is called
- Connection is cached and reused for performance

**Security Features:**
- Only SELECT queries allowed (no INSERT/UPDATE/DELETE)
- Maximum 1000 rows per query
- Credentials never exposed in tool responses

**Error Handling:**
- Clear error messages if credentials are missing
- Connection validation before each query
- Automatic reconnection if connection drops

## 📁 Files Updated

1. **manulife_mcp_server.py** - Added Snowflake tools and connection management
2. **requirements.txt** - Added snowflake-connector-python
3. **.env.example** - Template for Snowflake credentials
4. **README.md** - Complete documentation
5. **test_snowflake.py** - Connection test utility

## ❓ Troubleshooting

**"Missing required Snowflake credentials"**
→ Make sure SNOWFLAKE_ACCOUNT, USER, and PASSWORD are in .env

**"Failed to connect to DB"**
→ Check your account format. Try: `account.region` or `orgname-accountname`

**"Object does not exist"**
→ Verify database/schema names, or set them in .env

**Need more help?**
→ Check README.md for detailed troubleshooting

## 🎯 What's Next?

You can now:
- Query your Snowflake data through natural language
- Combine Snowflake data with other MCP tools
- Have AI analyze and visualize your data

The AI will automatically use the right Snowflake tools based on your questions!

---

**Need the detailed docs?** → See README.md
**Want to verify setup?** → Run `python test_snowflake.py`
