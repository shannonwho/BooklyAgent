#!/usr/bin/env python3
"""
Script to create Linear issues for System Prompt & Rules Enhancement.

Usage:
    python scripts/create_linear_issues.py

Requirements:
    - LINEAR_API_KEY environment variable
    - LINEAR_TEAM_ID environment variable (optional, will prompt if missing)
    
Setup:
    1. Get API key: Linear Settings → API → Personal API keys
    2. Get Team ID: Found in Linear URL (linear.app/team/{team-id}/...)
    3. Set environment variables:
       export LINEAR_API_KEY="your-api-key"
       export LINEAR_TEAM_ID="your-team-id"
"""

import os
import json
import requests
from typing import Optional, Dict, List
from dataclasses import dataclass

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass  # python-dotenv not installed, skip

# Linear GraphQL API endpoint
LINEAR_API_URL = "https://api.linear.app/graphql"

# Issue definitions based on the plan
ISSUES = [
    {
        "title": "Python/FastAPI Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for Python/FastAPI development in `.cursor/rules/python-patterns.mdc`

## Scope
- FastAPI route structure and organization
- Dependency injection patterns (`Depends`)
- Async/await best practices
- Pydantic models for request/response validation
- Router organization (`APIRouter`)
- HTTP status codes and exceptions
- Type hints for all functions
- Docstring conventions (Google style)

## File Location
`.cursor/rules/python-patterns.mdc`

## Key Patterns to Document
1. **Route Structure**
   - Use `APIRouter` for route organization
   - Group related endpoints in separate files (`/api/auth.py`, `/api/books.py`)
   - Use proper HTTP methods (`GET`, `POST`, `PUT`, `DELETE`)

2. **Dependency Injection**
   - Use `Depends(get_db)` for database sessions
   - Create reusable dependencies for authentication
   - Type hint all dependencies

3. **Async Patterns**
   - All route handlers should be `async def`
   - Use `await` for all async operations
   - Handle async context managers properly

4. **Pydantic Models**
   - Define request models (inherit from `BaseModel`)
   - Define response models
   - Use `EmailStr`, `Optional`, etc. for validation

## Reference Files
- `backend/api/auth.py`
- `backend/api/books.py`
- `backend/main.py`

## Acceptance Criteria
- [ ] File created with proper structure matching `react-patterns.mdc`
- [ ] All patterns documented with code examples from codebase
- [ ] Includes async/await patterns
- [ ] Includes Pydantic validation patterns
- [ ] Includes dependency injection patterns
- [ ] Cross-references related patterns in other files""",
        "priority": "High",
        "labels": ["documentation", "backend", "python", "fastapi"]
    },
    {
        "title": "Database/SQLAlchemy Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for SQLAlchemy async patterns in `.cursor/rules/database-patterns.mdc`

## Scope
- SQLAlchemy async patterns (`AsyncSession`)
- Model definition conventions
- Relationship definitions (`relationship`, `Mapped`)
- Query patterns (`select`, `filter`, `join`)
- Session management (`get_db` dependency)
- Transaction handling
- Enum usage for status fields

## File Location
`.cursor/rules/database-patterns.mdc`

## Key Patterns to Document
1. **Model Definition**
   - Use `Base` from `declarative_base()`
   - Define columns with proper types
   - Use `Mapped` for type hints
   - Use `relationship()` for associations

2. **Async Session Management**
   - Use `AsyncSession` from `sqlalchemy.ext.asyncio`
   - Use `get_db()` dependency for route handlers
   - Always close sessions properly

3. **Query Patterns**
   - Use `select()` for queries
   - Use `await session.execute()` for async queries
   - Use `scalars().all()` or `scalars().first()` for results

4. **Enums**
   - Use `str, Enum` for status fields
   - Define enums at module level
   - Use descriptive names

## Reference Files
- `backend/data/models.py`
- `backend/data/database.py`
- `backend/api/auth.py` (usage examples)

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] Async session patterns documented
- [ ] Model definition patterns documented
- [ ] Query patterns with examples
- [ ] Transaction handling patterns
- [ ] Cross-references API patterns""",
        "priority": "High",
        "labels": ["documentation", "backend", "database", "sqlalchemy"]
    },
    {
        "title": "API/WebSocket Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for REST API and WebSocket patterns in `.cursor/rules/api-patterns.mdc`

## Scope
- REST API endpoint structure
- WebSocket connection management
- Message handling patterns
- Connection lifecycle (connect, disconnect, error handling)
- Streaming patterns
- Session management for WebSockets

## File Location
`.cursor/rules/api-patterns.mdc`

## Key Patterns to Document
1. **REST API Structure**
   - Endpoint naming conventions
   - Request/response patterns
   - Error response format
   - Status code usage

2. **WebSocket Patterns**
   - Connection manager pattern
   - Message type handling
   - Error handling in async contexts
   - Session lifecycle management

3. **Streaming**
   - Streaming response patterns
   - Chunk handling
   - Error propagation

## Reference Files
- `backend/api/websocket.py`
- `backend/api/auth.py`
- `backend/api/books.py`

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] REST API patterns documented
- [ ] WebSocket patterns documented
- [ ] Connection lifecycle documented
- [ ] Error handling patterns included""",
        "priority": "High",
        "labels": ["documentation", "backend", "api", "websocket"]
    },
    {
        "title": "Error Handling Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for error handling in `.cursor/rules/error-handling.mdc`

## Scope
- Standardized error response format
- HTTPException usage patterns
- Error handling middleware
- Graceful degradation strategies
- User-friendly error messages
- Error logging patterns

## File Location
`.cursor/rules/error-handling.mdc`

## Key Patterns to Document
1. **Error Response Format**
   - Consistent structure across all endpoints
   - Include error code, message, details
   - Proper HTTP status codes

2. **HTTPException**
   - When to use `HTTPException`
   - Status code selection
   - Error message formatting

3. **Error Logging**
   - Structured logging
   - Error context
   - Log levels

## Reference Files
- `backend/api/auth.py` (error handling examples)
- `backend/api/websocket.py` (WebSocket error handling)

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] Standardized error format documented
- [ ] HTTPException patterns documented
- [ ] Logging patterns included
- [ ] Examples from codebase""",
        "priority": "High",
        "labels": ["documentation", "backend", "error-handling"]
    },
    {
        "title": "Security Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for security in `.cursor/rules/security-patterns.mdc`

## Scope
- JWT token handling
- Password hashing (bcrypt)
- Authentication dependencies
- Authorization patterns
- Input validation (Pydantic)
- CORS configuration
- Environment variable security

## File Location
`.cursor/rules/security-patterns.mdc`

## Key Patterns to Document
1. **Authentication**
   - JWT token generation and validation
   - Token expiration handling
   - Refresh token patterns

2. **Password Security**
   - Use bcrypt for hashing
   - Never store plain passwords
   - Password strength requirements

3. **Input Validation**
   - Use Pydantic for all inputs
   - Validate email addresses
   - Sanitize user inputs

## Reference Files
- `backend/api/auth.py`
- `backend/main.py` (CORS config)

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] JWT patterns documented
- [ ] Password hashing patterns documented
- [ ] Input validation patterns included
- [ ] Security best practices listed""",
        "priority": "High",
        "labels": ["documentation", "backend", "security"]
    },
    {
        "title": "Testing Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for testing in `.cursor/rules/testing-patterns.mdc`

## Scope
- Unit test structure (pytest)
- Async test patterns
- Test fixtures and factories
- Mocking patterns
- Integration test patterns
- Test database setup

## File Location
`.cursor/rules/testing-patterns.mdc`

## Key Patterns to Document
1. **Test Structure**
   - Use pytest for all tests
   - Organize tests by module
   - Use descriptive test names

2. **Async Tests**
   - Use `pytest.mark.asyncio`
   - Proper async fixture usage
   - Async context managers

3. **Fixtures**
   - Database fixtures
   - Client fixtures
   - Mock fixtures

## Reference Files
- `backend/tests/` (existing test files)

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] Pytest patterns documented
- [ ] Async test patterns included
- [ ] Fixture patterns documented
- [ ] Mocking strategies included""",
        "priority": "Medium",
        "labels": ["documentation", "testing"]
    },
    {
        "title": "Observability Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for observability in `.cursor/rules/observability-patterns.mdc`

## Scope
- OpenTelemetry instrumentation
- Structured logging patterns
- Tracing patterns
- Metrics collection
- Error tracking
- Performance monitoring

## File Location
`.cursor/rules/observability-patterns.mdc`

## Key Patterns to Document
1. **OpenTelemetry**
   - Span creation
   - Trace context propagation
   - Attribute setting

2. **Logging**
   - Structured logging format
   - Log levels
   - Context inclusion

3. **Metrics**
   - Counter usage
   - Histogram usage
   - Metric naming

## Reference Files
- `backend/telemetry/`
- `backend/agent/controller.py` (instrumentation examples)

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] OpenTelemetry patterns documented
- [ ] Logging patterns included
- [ ] Metrics patterns documented
- [ ] Examples from codebase""",
        "priority": "Medium",
        "labels": ["documentation", "observability", "telemetry"]
    },
    {
        "title": "Agent Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for agent-specific patterns in `.cursor/rules/agent-patterns.mdc`

## Scope
- Agent controller structure
- Tool definition patterns
- Tool execution patterns
- Conversation state management
- Session management
- Context injection patterns
- Fallback handling (Anthropic → OpenAI)

## File Location
`.cursor/rules/agent-patterns.mdc`

## Key Patterns to Document
1. **Agent Controller**
   - Controller initialization
   - Message processing flow
   - Tool execution loop

2. **Tool Definition**
   - Tool schema structure
   - Input validation
   - Output formatting

3. **Conversation Management**
   - History tracking
   - Context injection
   - Session persistence

## Reference Files
- `backend/agent/controller.py`
- `backend/agent/tools.py`
- `backend/agent/prompts.py`

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] Agent controller patterns documented
- [ ] Tool patterns documented
- [ ] Conversation management patterns included
- [ ] Fallback patterns documented""",
        "priority": "Medium",
        "labels": ["documentation", "backend", "agent", "ai"]
    },
    {
        "title": "Code Organization Patterns Documentation",
        "description": """## Overview
Create comprehensive pattern documentation for code organization in `.cursor/rules/code-organization.mdc`

## Scope
- Backend module structure (`/api`, `/data`, `/agent`, `/telemetry`)
- Import organization
- Circular dependency prevention
- File naming conventions
- Package structure

## File Location
`.cursor/rules/code-organization.mdc`

## Key Patterns to Document
1. **Module Structure**
   - Backend directory organization
   - Frontend directory organization
   - Separation of concerns

2. **Import Organization**
   - Standard library imports first
   - Third-party imports second
   - Local imports last
   - Absolute vs relative imports

3. **Naming Conventions**
   - File naming
   - Module naming
   - Class/function naming

## Reference Files
- Project root structure
- `backend/` directory
- `frontend/src/` directory

## Acceptance Criteria
- [ ] File created with proper structure
- [ ] Module structure documented
- [ ] Import patterns documented
- [ ] Naming conventions included
- [ ] Examples from codebase""",
        "priority": "Low",
        "labels": ["documentation", "code-organization"]
    },
    {
        "title": "Enhance React Patterns Documentation",
        "description": """## Overview
Enhance existing React patterns documentation in `.cursor/rules/react-patterns.mdc`

## Scope
- Form handling patterns (react-hook-form if used)
- Loading state patterns
- Error boundary implementation
- Component composition patterns
- WebSocket client patterns
- State synchronization patterns

## File Location
`.cursor/rules/react-patterns.mdc` (update existing)

## Key Patterns to Add
1. **Form Handling**
   - Form validation
   - Error display
   - Submission handling

2. **Loading States**
   - Loading indicators
   - Skeleton screens
   - Optimistic updates

3. **Error Boundaries**
   - Error boundary component
   - Error recovery
   - Error reporting

4. **WebSocket Client**
   - Connection management
   - Message handling
   - Reconnection logic

## Reference Files
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/store/chatStore.ts`
- `frontend/src/components/chat/ChatWidget.tsx`

## Acceptance Criteria
- [ ] Existing patterns preserved
- [ ] New patterns added
- [ ] Examples from codebase included
- [ ] Consistent formatting maintained""",
        "priority": "Low",
        "labels": ["documentation", "frontend", "react"]
    }
]


@dataclass
class LinearConfig:
    """Configuration for Linear API."""
    api_key: str
    team_id: Optional[str] = None


def get_team_id(api_key: str) -> Optional[str]:
    """Query Linear API to get team ID."""
    query = """
    query {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    
    response = requests.post(
        LINEAR_API_URL,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        json={"query": query}
    )
    
    if response.status_code != 200:
        print(f"Error fetching teams: {response.text}")
        return None
    
    data = response.json()
    teams = data.get("data", {}).get("teams", {}).get("nodes", [])
    
    if not teams:
        print("No teams found")
        return None
    
    print("\nAvailable teams:")
    for i, team in enumerate(teams, 1):
        print(f"{i}. {team['name']} (ID: {team['id']}, Key: {team['key']})")
    
    if len(teams) == 1:
        return teams[0]['id']
    
    choice = input("\nEnter team number: ").strip()
    try:
        idx = int(choice) - 1
        return teams[idx]['id']
    except (ValueError, IndexError):
        print("Invalid choice")
        return None


def create_epic(api_key: str, team_id: str) -> Optional[str]:
    """Create the parent epic."""
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
        }
      }
    }
    """
    
    variables = {
        "input": {
            "teamId": team_id,
            "title": "System Prompt & Rules Enhancement",
            "description": """Enhance Cursor rules system by adding comprehensive backend patterns and improving existing frontend patterns.

**Goals**:
- Document Python/FastAPI patterns
- Establish database/SQLAlchemy conventions
- Standardize error handling
- Add testing, security, and observability patterns
- Improve agent-specific patterns

**Success Criteria**:
- All backend code patterns documented
- Rules consistent with codebase
- Rules actionable with examples
- Rules complement existing React patterns""",
            "priority": 1,  # High priority
        }
    }
    
    response = requests.post(
        LINEAR_API_URL,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        json={"query": mutation, "variables": variables}
    )
    
    if response.status_code != 200:
        print(f"Error creating epic: {response.text}")
        return None
    
    data = response.json()
    if errors := data.get("errors"):
        print(f"GraphQL errors: {errors}")
        return None
    
    issue = data.get("data", {}).get("issueCreate", {}).get("issue")
    if issue:
        print(f"✓ Created epic: {issue['identifier']}")
        return issue['id']
    
    return None


def create_issue(api_key: str, team_id: str, epic_id: Optional[str], issue_data: Dict) -> bool:
    """Create a single Linear issue."""
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
        }
      }
    }
    """
    
    priority_map = {
        "High": 1,
        "Medium": 2,
        "Low": 3,
    }
    
    input_data = {
        "teamId": team_id,
        "title": issue_data["title"],
        "description": issue_data["description"],
        "priority": priority_map.get(issue_data.get("priority", "Medium"), 2),
    }
    
    if epic_id:
        input_data["parentId"] = epic_id
    
    variables = {"input": input_data}
    
    response = requests.post(
        LINEAR_API_URL,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        json={"query": mutation, "variables": variables}
    )
    
    if response.status_code != 200:
        print(f"✗ Error creating issue '{issue_data['title']}': {response.text}")
        return False
    
    data = response.json()
    if errors := data.get("errors"):
        print(f"✗ GraphQL errors for '{issue_data['title']}': {errors}")
        return False
    
    issue = data.get("data", {}).get("issueCreate", {}).get("issue")
    if issue:
        print(f"✓ Created issue: {issue['identifier']} - {issue['title']}")
        return True
    
    return False


def main():
    """Main function to create Linear issues."""
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY environment variable not set")
        print("\nTo get your API key:")
        print("1. Go to Linear Settings → API → Personal API keys")
        print("2. Create a new API key")
        print("3. Set it: export LINEAR_API_KEY='your-key-here'")
        return
    
    # Ensure API key has Bearer prefix
    if not api_key.startswith("Bearer "):
        api_key = f"Bearer {api_key}"
    
    team_id = os.getenv("LINEAR_TEAM_ID")
    if not team_id:
        print("LINEAR_TEAM_ID not set, fetching teams...")
        team_id = get_team_id(api_key)
        if not team_id:
            print("Failed to get team ID")
            return
        print(f"\nUsing team ID: {team_id}")
        print("You can set this for next time: export LINEAR_TEAM_ID='{team_id}'")
    
    print("\n" + "="*60)
    print("Creating Linear Issues for System Prompt Improvements")
    print("="*60 + "\n")
    
    # Create epic first
    print("Creating epic...")
    epic_id = create_epic(api_key, team_id)
    if not epic_id:
        print("Failed to create epic, continuing without parent...")
    
    print(f"\nCreating {len(ISSUES)} issues...\n")
    
    # Create all issues
    success_count = 0
    for issue_data in ISSUES:
        if create_issue(api_key, team_id, epic_id, issue_data):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: Created {success_count}/{len(ISSUES)} issues")
    if epic_id:
        print(f"Epic created with ID: {epic_id}")
    print("="*60)


if __name__ == "__main__":
    main()
