import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def detailed_connection_test():
    """Test connection with detailed logging of all messages"""
    
    print("=" * 70)
    print("Detailed MCP Connection Test")
    print("=" * 70)
    
    server_script = Path("manulife_mcp_server.py").resolve()
    
    print(f"\n📁 Server: {server_script}")
    
    server_params = StdioServerParameters(
        command="fastmcp",
        args=["run", str(server_script)],
        env=None
    )
    
    print("\n🔌 Starting server process...")
    
    try:
        exit_stack = stdio_client(server_params)
        read_stream, write_stream = await exit_stack.__aenter__()
        
        print("✅ Server process started")
        print("📡 Creating ClientSession...")
        
        session = ClientSession(read_stream, write_stream)
        
        print("📤 Calling session.initialize()...")
        print("   (This sends the 'initialize' JSON-RPC request)")
        
        # Try initialize with detailed error catching
        try:
            result = await asyncio.wait_for(
                session.initialize(), 
                timeout=10
            )
            print("✅ Initialize successful!")
            print(f"   Protocol version: {result.protocolVersion}")
            print(f"   Server capabilities: {result.capabilities}")
            
        except asyncio.TimeoutError:
            print("❌ TIMEOUT waiting for initialize response")
            print("\n🔍 Checking if we can read anything from stdout...")
            
            # Try to read raw data
            try:
                raw_line = await asyncio.wait_for(
                    read_stream.readline(),
                    timeout=2
                )
                if raw_line:
                    print(f"   Raw data received: {raw_line.decode()[:200]}")
                else:
                    print("   No data available")
            except asyncio.TimeoutError:
                print("   No data received (timeout)")
            except Exception as e:
                print(f"   Error reading: {e}")
            
            raise
        
        print("\n📤 Calling session.list_tools()...")
        tools_response = await asyncio.wait_for(
            session.list_tools(),
            timeout=5
        )
        
        print(f"✅ Found {len(tools_response.tools)} tools:")
        for tool in tools_response.tools:
            print(f"   • {tool.name}")
        
        print("\n🎉 SUCCESS! Connection is fully working!")
        
        # Cleanup
        await exit_stack.__aexit__(None, None, None)
        
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT ERROR")
        print("\nPossible causes:")
        print("  1. Server is not sending responses in correct format")
        print("  2. Session.initialize() is waiting for something that never comes")
        print("  3. Protocol version mismatch")
        
        print("\n🔧 Let's test the server manually...")
        print("\nTry this command in another terminal:")
        print(f"  fastmcp run {server_script}")
        print("\nThen type this JSON and press Enter:")
        print('  {"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')
        print("\nYou should see a JSON response immediately.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(detailed_connection_test())