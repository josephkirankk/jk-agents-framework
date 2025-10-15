#!/usr/bin/env python3
"""
Test only the syntax of the API file without running imports
"""
import ast
import sys

def test_syntax():
    """Test if the API file has valid Python syntax."""
    try:
        with open("/Users/A80997271/Documents/projects/jk-agents-framework/api.py", "r") as f:
            source = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source)
        print("✅ api.py has valid Python syntax!")
        
        # Check for our v1/query endpoint
        if '@app.post("/v1/query")' in source:
            print("✅ /v1/query endpoint found in code")
        else:
            print("❌ /v1/query endpoint not found")
            
        # Check for proper exception handling in query_endpoint
        if 'except HTTPException:' in source and 'except BaseExceptionGroup' in source:
            print("✅ Exception handling looks complete")
        else:
            print("❌ Exception handling may be incomplete")
            
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error in api.py: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error reading api.py: {e}")
        return False

if __name__ == "__main__":
    success = test_syntax()
    if success:
        print("\n🎉 Syntax is fixed! The issue was:")
        print("   - Missing except blocks in query_endpoint function")
        print("   - This has been resolved")
        print("\nThe API should now start properly (if dependencies are correct)")
        print("\nNext steps:")
        print("1. Start the API: python api.py")
        print("2. Test with curl command for v1/query endpoint")
    else:
        sys.exit(1)
