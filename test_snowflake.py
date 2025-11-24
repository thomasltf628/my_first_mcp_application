"""
Test Snowflake Connection
Run this script to verify your Snowflake credentials before running the full MCP application.
"""

import os
from dotenv import load_dotenv
import snowflake.connector

def test_connection():
    print("🧪 Testing Snowflake Connection...\n")
    
    # Load environment variables
    load_dotenv()
    
    # Check for required credentials
    required_vars = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease check your .env file and ensure these variables are set:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    # Get credentials
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    role = os.getenv("SNOWFLAKE_ROLE")
    
    print("📋 Configuration:")
    print(f"  Account: {account}")
    print(f"  User: {user}")
    print(f"  Warehouse: {warehouse}")
    print(f"  Database: {database or 'Not specified'}")
    print(f"  Schema: {schema}")
    print(f"  Role: {role or 'Not specified'}")
    print()
    
    try:
        # Build connection parameters
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
        
        print("🔌 Connecting to Snowflake...")
        conn = snowflake.connector.connect(**conn_params)
        print("✅ Connection successful!\n")
        
        # Test query
        cursor = conn.cursor()
        
        print("🔍 Running test queries...\n")
        
        # Get Snowflake version
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"  Snowflake Version: {version}")
        
        # Get current user
        cursor.execute("SELECT CURRENT_USER()")
        current_user = cursor.fetchone()[0]
        print(f"  Current User: {current_user}")
        
        # Get current role
        cursor.execute("SELECT CURRENT_ROLE()")
        current_role = cursor.fetchone()[0]
        print(f"  Current Role: {current_role}")
        
        # Get current warehouse
        cursor.execute("SELECT CURRENT_WAREHOUSE()")
        current_warehouse = cursor.fetchone()[0]
        print(f"  Current Warehouse: {current_warehouse}")
        
        # Get current database
        cursor.execute("SELECT CURRENT_DATABASE()")
        current_database = cursor.fetchone()[0]
        print(f"  Current Database: {current_database or 'None'}")
        
        # Get current schema
        cursor.execute("SELECT CURRENT_SCHEMA()")
        current_schema = cursor.fetchone()[0]
        print(f"  Current Schema: {current_schema or 'None'}")
        
        print()
        
        # Try to list tables if database is set
        if current_database:
            print("📊 Listing tables in current database/schema...")
            try:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                if tables:
                    print(f"  Found {len(tables)} tables:")
                    for i, table in enumerate(tables[:5], 1):  # Show first 5
                        print(f"    {i}. {table[1]}")  # table[1] is table name
                    if len(tables) > 5:
                        print(f"    ... and {len(tables) - 5} more")
                else:
                    print("  No tables found (this is OK if database is empty)")
            except Exception as e:
                print(f"  Could not list tables: {e}")
                print("  (This is OK - may need database/schema permissions)")
        else:
            print("ℹ️  No database set - skipping table listing")
        
        print()
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("✅ All tests passed! Your Snowflake connection is working correctly.")
        print("\nYou can now run the MCP application with: python raw_mcp_client.py")
        return True
        
    except snowflake.connector.errors.ProgrammingError as e:
        print(f"❌ Snowflake Error: {e}")
        print("\nCommon issues:")
        print("  - Check your account identifier format (try both formats)")
        print("  - Verify username and password are correct")
        print("  - Ensure warehouse name is correct")
        print("  - Check if user has required permissions")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check:")
        print("  1. Your .env file has correct credentials")
        print("  2. Your account identifier is in the correct format")
        print("  3. Your network allows connections to Snowflake")
        print("  4. You're connected to VPN if required")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
