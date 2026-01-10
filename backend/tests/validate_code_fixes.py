#!/usr/bin/env python3
"""Code validation to verify bug fixes are in place."""
import os
import re
import sys


def check_file_contains(file_path, patterns, description):
    """Check if file contains required patterns."""
    try:
        # Resolve absolute path
        abs_path = os.path.abspath(file_path)
        with open(abs_path, 'r') as f:
            content = f.read()
        
        results = []
        for pattern, expected in patterns:
            found = bool(re.search(pattern, content, re.MULTILINE))
            results.append((found, expected))
            if not found:
                print(f"  ✗ Missing: {expected}")
            else:
                print(f"  ✓ Found: {expected}")
        
        return all(found for found, _ in results)
    except FileNotFoundError:
        print(f"  ✗ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        return False


def test_1_agent_optional_db():
    """Test 1: AgentController accepts optional db parameter."""
    print("\n[Test 1] Validating AgentController optional db parameter...")
    file_path = "backend/agent/controller.py"
    
    patterns = [
        (r'def __init__\(self, session_id: str, db: Optional\[AsyncSession\] = None\)', 
         "Optional db parameter in __init__"),
        (r'self\.db = db', 
         "db assignment"),
    ]
    
    return check_file_contains(file_path, patterns, "AgentController optional db")


def test_2_websocket_no_db_on_connect():
    """Test 2: WebSocket connect creates agent without db session."""
    print("\n[Test 2] Validating WebSocket agent creation without db...")
    file_path = "backend/api/websocket.py"
    
    patterns = [
        (r'self\.agents\[session_id\] = AgentController\(session_id\)', 
         "AgentController created without db session"),
        (r'# Create agent for this session.*without db session', 
         "Comment indicating no db session"),
    ]
    
    return check_file_contains(file_path, patterns, "WebSocket agent creation")


def test_3_db_session_per_message():
    """Test 3: Database session created per message."""
    print("\n[Test 3] Validating db session created per message...")
    file_path = "backend/api/websocket.py"
    
    patterns = [
        (r'async with AsyncSessionLocal\(\) as db:', 
         "AsyncSessionLocal context manager"),
        (r'agent\.db = db', 
         "Db session assigned to agent"),
        (r'async for chunk in agent\.process_message', 
         "process_message called with db session"),
    ]
    
    return check_file_contains(file_path, patterns, "Db session per message")


def test_4_user_email_passing():
    """Test 4: User email passed correctly in SupportPage."""
    print("\n[Test 4] Validating user email passing in SupportPage...")
    file_path = "frontend/src/pages/SupportPage.tsx"
    
    patterns = [
        (r'connect\(isAuthenticated \? user\?\.email : undefined\)', 
         "connect called with user.email"),
        (r'sendMessage\(.*isAuthenticated \? user\?\.email : undefined\)', 
         "sendMessage called with user.email"),
    ]
    
    return check_file_contains(file_path, patterns, "User email passing")


def test_5_email_auto_injection():
    """Test 5: Email auto-injection logic in controller."""
    print("\n[Test 5] Validating email auto-injection logic...")
    file_path = "backend/agent/controller.py"
    
    patterns = [
        (r'tools_that_need_email', 
         "Tools that need email list"),
        (r'if self\.user_email and tool_use\.name in tools_that_need_email', 
         "Email injection condition"),
        (r'tool_input\["email"\] = self\.user_email', 
         "Email assignment to tool_input"),
    ]
    
    return check_file_contains(file_path, patterns, "Email auto-injection")


def test_6_isloading_fix():
    """Test 6: isLoading mapped from isTyping."""
    print("\n[Test 6] Validating isLoading fix...")
    file_path = "frontend/src/pages/SupportPage.tsx"
    
    patterns = [
        (r'isTyping: isLoading', 
         "isTyping mapped to isLoading"),
    ]
    
    return check_file_contains(file_path, patterns, "isLoading mapping")


def test_7_db_check_before_tool_execution():
    """Test 7: Database session check before tool execution."""
    print("\n[Test 7] Validating db session check before tool execution...")
    file_path = "backend/agent/controller.py"
    
    patterns = [
        (r'if not self\.db:', 
         "Db session check"),
        (r'"content": "Database session not available', 
         "Error message for missing db"),
    ]
    
    return check_file_contains(file_path, patterns, "Db session validation")


def main():
    """Run all code validation tests."""
    print("="*70)
    print("Support Agent Bug Fix Code Validation")
    print("="*70)
    print("\nValidating that bug fixes are present in the codebase...")
    
    # Change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    os.chdir(project_root)
    
    results = []
    
    results.append(("Test 1: Agent optional db parameter", test_1_agent_optional_db()))
    results.append(("Test 2: WebSocket agent creation without db", test_2_websocket_no_db_on_connect()))
    results.append(("Test 3: Db session per message", test_3_db_session_per_message()))
    results.append(("Test 4: User email passing", test_4_user_email_passing()))
    results.append(("Test 5: Email auto-injection", test_5_email_auto_injection()))
    results.append(("Test 6: isLoading fix", test_6_isloading_fix()))
    results.append(("Test 7: Db check before tool execution", test_7_db_check_before_tool_execution()))
    
    # Summary
    print("\n" + "="*70)
    print("Validation Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All code validations passed! Bug fixes are present in codebase.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please review the code.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
