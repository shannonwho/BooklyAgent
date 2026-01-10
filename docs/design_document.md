# Bookly Customer Support Agent - Design Document

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Agent Design](#agent-design)
4. [Prompt Engineering](#prompt-engineering)
5. [Tool Definitions](#tool-definitions)
6. [Multi-Turn Conversation Handling](#multi-turn-conversation-handling)
7. [Personalization Strategy](#personalization-strategy)
8. [Safety & Grounding](#safety--grounding)
9. [Edge Cases](#edge-cases)
10. [Testing Strategy](#testing-strategy)

---

## Overview

Bookly is a demo online bookstore with an integrated AI-powered customer support agent. The agent uses Claude's tool-use capabilities to provide accurate, personalized assistance while maintaining strict grounding in real data.

### Key Capabilities
- Order tracking and status inquiries
- Return initiation and policy questions
- Personalized book recommendations
- Account and profile assistance
- General support ticket creation

### Design Principles
1. **Data Grounding**: Never hallucinate - all facts come from tools
2. **Clarity-First**: Ask clarifying questions when ambiguous
3. **User-Centric**: Personalize responses based on user context
4. **Graceful Degradation**: Handle edge cases without breaking

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Bookstore   │  │  Chat Widget │  │   Support Page       │  │
│  │  (REST API)  │  │  (WebSocket) │  │   (WebSocket)        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer                               │  │
│  │  /api/auth  /api/books  /api/cart  /api/orders  /ws/chat  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │                   Agent Controller                         │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │   System    │  │    Tool      │  │    Session      │  │  │
│  │  │   Prompt    │  │   Executor   │  │    Manager      │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │                    Data Layer                              │  │
│  │  Books │ Customers │ Orders │ Cart │ Policies │ Tickets   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │    Claude API    │
                        │  (Tool Use Mode) │
                        └──────────────────┘
```

### Communication Flow

1. **User sends message** → WebSocket receives message
2. **Agent Controller** → Adds user context (if authenticated)
3. **Claude API call** → With tools and conversation history
4. **Tool execution loop** → Execute any tool calls, return results
5. **Response streaming** → Stream final response to frontend
6. **Session update** → Store conversation in session manager

---

## Agent Design

### Conversation State Machine

```
                    ┌─────────────┐
                    │   IDLE      │
                    └──────┬──────┘
                           │ User message
                           ▼
                    ┌─────────────┐
              ┌─────│  ANALYZING  │─────┐
              │     └─────────────┘     │
              │                         │
    Need clarification            Have enough info
              │                         │
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │   ASKING    │          │  EXECUTING  │
       └──────┬──────┘          └──────┬──────┘
              │                        │
        User responds             Tool results
              │                        │
              └────────────┬───────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ RESPONDING  │──────┐
                    └─────────────┘      │
                           │             │
                    ┌──────┴──────┐      │
                    ▼             ▼      │
              ┌─────────┐  ┌──────────┐  │
              │ COMPLETE│  │MORE TOOLS│──┘
              └─────────┘  └──────────┘
```

### Intent Classification

The agent implicitly classifies user intents based on message content:

| Intent Category | Trigger Patterns | Primary Tools |
|-----------------|------------------|---------------|
| Order Status | "where's my order", "tracking", "order #" | `search_orders`, `get_order_status` |
| Returns | "return", "refund", "exchange" | `get_order_status`, `get_policy_info`, `initiate_return` |
| Recommendations | "recommend", "suggest", "what should I read" | `get_customer_info`, `get_recommendations` |
| Policy Questions | "shipping policy", "return policy", "how long" | `get_policy_info` |
| Account Help | "password", "account", "profile" | `get_customer_info` |
| Escalation | "speak to human", "manager", frustrated language | `create_support_ticket` |

---

## Prompt Engineering

### System Prompt Structure

```
┌────────────────────────────────────────────────────────────────┐
│                      SYSTEM PROMPT                              │
├────────────────────────────────────────────────────────────────┤
│  1. ROLE DEFINITION                                            │
│     - Identity: Bookly customer support agent                  │
│     - Personality: Friendly, helpful, professional             │
│     - Boundaries: What you can/cannot do                       │
├────────────────────────────────────────────────────────────────┤
│  2. CAPABILITIES                                               │
│     - Order tracking and status                                │
│     - Return processing                                        │
│     - Book recommendations                                     │
│     - Policy information                                       │
├────────────────────────────────────────────────────────────────┤
│  3. TOOL USAGE RULES                                           │
│     - ALWAYS use tools for factual queries                     │
│     - NEVER fabricate order numbers, dates, etc.               │
│     - Return "not found" if data doesn't exist                 │
├────────────────────────────────────────────────────────────────┤
│  4. CONVERSATION GUIDELINES                                    │
│     - When to ask vs. when to act                              │
│     - How to handle ambiguity                                  │
│     - Multi-turn reference resolution                          │
├────────────────────────────────────────────────────────────────┤
│  5. SAFETY RULES                                               │
│     - No personal data disclosure                              │
│     - Escalation triggers                                      │
│     - Out-of-scope handling                                    │
└────────────────────────────────────────────────────────────────┘
```

### Prompt Design Decisions

**1. Explicit Tool Grounding**
```
IMPORTANT: You MUST use tools to look up any factual information.
Never make up order numbers, tracking info, prices, or policies.
If a tool returns no results, tell the user you couldn't find
the information - never fabricate data.
```

**2. Clarification Protocol**
```
When to ASK for clarification:
- Multiple orders exist and user says "my order"
- Ambiguous product reference
- Missing required information (email for guest users)

When to ACT without asking:
- Single order exists for user
- User provides specific order number
- Simple policy questions
```

**3. Personalization Injection**
```
Context injection format:
"The user {name} is logged in. They have ordered from us {n} times.
Their favorite genres are: {genres}. Recent purchases: {titles}."
```

---

## Tool Definitions

### Tool Schema

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|
| `get_order_status` | Get details for specific order | `order_id: int` | Order object with status, items, tracking |
| `search_orders` | Find orders by email | `email: str` | List of order summaries |
| `get_customer_info` | Get customer profile | `customer_id: int` | Profile with preferences, history |
| `initiate_return` | Start return process | `order_id: int`, `reason: str` | Confirmation or rejection |
| `get_policy_info` | Get store policies | `policy_type: str` | Policy details |
| `get_recommendations` | Get personalized suggestions | `customer_id?: int`, `genre?: str` | List of book recommendations |
| `search_books` | Search book catalog | `query: str`, `genre?: str` | List of matching books |
| `create_support_ticket` | Escalate to human | `customer_id?: int`, `issue: str` | Ticket confirmation |

### Tool Execution Flow

```python
async def process_message(self, message: str) -> AsyncGenerator[str, None]:
    # 1. Add message to conversation history
    self.conversation_history.append({"role": "user", "content": message})

    # 2. Call Claude API with tools
    response = await self.client.messages.create(
        model="claude-sonnet-4-20250514",
        system=self.system_prompt,
        messages=self.conversation_history,
        tools=TOOL_DEFINITIONS,
        max_tokens=1024,
    )

    # 3. Tool use loop
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = await execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        # Continue conversation with tool results
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            system=self.system_prompt,
            messages=[...self.conversation_history,
                      {"role": "assistant", "content": response.content},
                      {"role": "user", "content": tool_results}],
            tools=TOOL_DEFINITIONS,
            max_tokens=1024,
        )

    # 4. Extract and stream final response
    final_text = extract_text(response.content)
    yield final_text
```

---

## Multi-Turn Conversation Handling

### Reference Resolution

The agent handles anaphoric references (pronouns, demonstratives) through conversation context:

**Example: Order Tracking Multi-Turn**
```
User: "Where's my order?"
Agent: [Uses search_orders with user's email]
       "I found 3 recent orders. Which one are you asking about?
        1. ORD-2024-001 - Shipped (The Great Gatsby)
        2. ORD-2024-002 - Delivered (1984)
        3. ORD-2024-003 - Processing (Dune)"

User: "The first one"
Agent: [Uses get_order_status for ORD-2024-001]
       "Your order ORD-2024-001 shipped on Jan 5th.
        Tracking: 1Z999AA10123456784
        Expected delivery: Jan 8th"

User: "Can I return it?"
Agent: [Uses get_policy_info + get_order_status]
       "This order is still in transit. Once delivered, you have
        30 days to initiate a return. Would you like me to set
        a reminder?"
```

### Session State Management

```python
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def get_or_create(self, session_id: str, user_id: int = None) -> ChatSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(
                session_id=session_id,
                user_id=user_id,
                conversation_history=[],
                context={},
                created_at=datetime.utcnow()
            )
        return self.sessions[session_id]
```

### Context Carryover

Key context preserved across turns:
- **Referenced orders**: "that order" → most recently discussed
- **User identity**: Logged-in user info persists
- **Topic continuity**: "what about shipping?" continues current order discussion
- **Preferences stated**: "I like mystery books" remembered for recommendations

---

## Personalization Strategy

### Data Sources for Personalization

| Source | Data Points | Usage |
|--------|-------------|-------|
| User Profile | `favorite_genres`, `name` | Recommendations, greeting |
| Order History | Past purchases, frequency | "Based on your history..." |
| Current Session | Stated preferences, questions | In-conversation learning |
| Browsing Context | Current page, viewed books | "I see you're looking at..." |

### Recommendation Algorithm

```python
async def get_recommendations(customer_id: int = None, genre: str = None):
    recommendations = []

    if customer_id:
        # 1. Get user preferences
        customer = await get_customer(customer_id)
        preferred_genres = customer.favorite_genres
        purchased_ids = [o.book_id for o in customer.orders]

        # 2. Find books in preferred genres, not purchased
        for genre in preferred_genres:
            genre_books = await get_books_by_genre(genre)
            for book in genre_books:
                if book.id not in purchased_ids:
                    recommendations.append(book)

    if genre:
        # Add genre-specific recommendations
        genre_books = await get_books_by_genre(genre)
        recommendations.extend(genre_books)

    # 3. Fill with popular/trending if needed
    if len(recommendations) < 5:
        popular = await get_popular_books()
        recommendations.extend(popular)

    return recommendations[:10]
```

### Personalized Response Examples

**Cold Start (No preferences)**
```
User: "Can you recommend a book?"
Agent: "I'd love to help! To give you better recommendations,
        what genres do you enjoy? Some popular options are:
        - Mystery & Thriller
        - Science Fiction
        - Romance
        - Non-fiction / Self-help"
```

**Warm User (Has preferences)**
```
User: "Can you recommend a book?"
Agent: [Uses get_customer_info, get_recommendations]
       "Based on your love of Mystery and Sci-Fi, I think you'd
        enjoy 'Project Hail Mary' by Andy Weir - it combines
        scientific problem-solving with a gripping mystery!

        Also consider:
        - 'The Silent Patient' (Thriller)
        - 'Dark Matter' (Sci-Fi Mystery)"
```

---

## Safety & Grounding

### Hallucination Prevention

**Rule 1: Tool-Grounded Facts**
```
NEVER generate:
- Order numbers (use search_orders)
- Tracking numbers (use get_order_status)
- Prices (use search_books)
- Policy details (use get_policy_info)
- Delivery dates (use get_order_status)
```

**Rule 2: Explicit Uncertainty**
```
When data not found, respond with:
"I couldn't find any orders matching that description.
Could you double-check the order number or email address?"

NOT: "Your order #12345 is on the way!" (fabricated)
```

**Rule 3: Tool Verification**
```python
# In tool execution
if not result:
    return {
        "success": False,
        "error": "No matching records found",
        "suggestion": "Please verify the provided information"
    }
```

### Data Privacy

**What the agent CAN access:**
- User's own orders and profile (when authenticated)
- Public book information
- General store policies

**What the agent CANNOT do:**
- Access other users' orders
- Reveal full payment information
- Modify data without confirmation
- Share conversation data

### Escalation Triggers

| Trigger | Action |
|---------|--------|
| User explicitly requests human | Create ticket, acknowledge |
| 3+ failed resolution attempts | Offer escalation proactively |
| Sensitive issues (fraud, harassment) | Immediate escalation |
| Out-of-scope requests | Politely decline, offer alternatives |

### Out-of-Scope Handling

```
User: "Can you help me hack my ex's account?"
Agent: "I'm sorry, but I can't help with that request. I'm here
        to assist with Bookly-related questions like order tracking,
        returns, and book recommendations. Is there anything else
        I can help you with today?"
```

---

## Edge Cases

### Test Scenarios by User Profile

| User | Edge Case | Expected Behavior |
|------|-----------|-------------------|
| David Kim | No orders | "I don't see any orders for your account" |
| Alex Taylor | No preferences | Cold-start recommendations flow |
| Olivia Smith | Return already processed | "This order was already returned" |
| Emma Wilson | Order too old for return | "This order is outside our 30-day window" |
| Rachel Brown | Open support ticket | "I see you have an open ticket #X..." |
| James Garcia | New customer | Welcome messaging, gentle onboarding |
| Sarah Johnson | Multiple pending orders | Disambiguation flow |
| Sophia Martinez | Heavy history | Pagination, diverse recommendations |

### Error Handling

```python
async def execute_tool(tool_name: str, params: dict) -> dict:
    try:
        result = await TOOL_HANDLERS[tool_name](**params)
        return {"success": True, "data": result}
    except NotFoundException:
        return {
            "success": False,
            "error": "not_found",
            "message": f"No {tool_name.replace('_', ' ')} found"
        }
    except ValidationError as e:
        return {
            "success": False,
            "error": "invalid_input",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {
            "success": False,
            "error": "internal_error",
            "message": "Something went wrong. Please try again."
        }
```

### Conversation Recovery

**Handling Non-Sequiturs**
```
User: "What's the weather?"
Agent: "I'm a Bookly support assistant, so I can't check the weather.
        But I can help you with:
        - Tracking your orders
        - Book recommendations
        - Returns and refunds
        What can I assist you with?"
```

**Handling Frustration**
```
# Detect frustration signals
frustration_indicators = [
    "this is ridiculous",
    "waste of time",
    "speak to a human",
    "!!" (multiple exclamation)
]

# Response
"I understand this is frustrating, and I apologize for the
difficulty. Would you like me to create a support ticket so
a team member can follow up with you directly?"
```

---

## Testing Strategy

### Automated Test Cases

```python
# Test: Order lookup - authenticated user
async def test_order_lookup_authenticated():
    agent = AgentController(user_id=1)  # Sarah Johnson
    response = await agent.process("Where's my order?")
    assert "ORD-" in response  # Should return real order numbers
    assert "fabricated" not in response.lower()

# Test: No orders found
async def test_no_orders_user():
    agent = AgentController(user_id=6)  # David Kim - no orders
    response = await agent.process("Where's my order?")
    assert "couldn't find" in response.lower() or "no orders" in response.lower()

# Test: Return eligibility
async def test_return_eligibility():
    agent = AgentController(user_id=5)  # Olivia Smith - has returns
    response = await agent.process("I want to return order ORD-2024-005")
    # Should check policy and status
    assert "return" in response.lower()
```

### Manual Testing Checklist

- [ ] Multi-turn order tracking with disambiguation
- [ ] Return flow with policy verification
- [ ] Personalized recommendations (logged in vs guest)
- [ ] Edge case: no orders found
- [ ] Edge case: order outside return window
- [ ] Edge case: already returned order
- [ ] Escalation to human support
- [ ] Out-of-scope request handling
- [ ] Tool failure recovery

### Demo Script

1. **Guest Flow**: Browse books → Ask for recommendations → Get cold-start flow
2. **Login Flow**: Login as Sarah → See personalized "For You" section
3. **Order Inquiry**: "Where's my order?" → Disambiguation → Details
4. **Return Request**: "I want to return this" → Policy check → Process
5. **Recommendation**: "Suggest a book" → Personalized based on history
6. **Escalation**: "I need to speak to a human" → Ticket creation

---

## Appendix

### A. Complete Tool Schemas

```python
TOOL_DEFINITIONS = [
    {
        "name": "get_order_status",
        "description": "Get detailed status and information for a specific order by ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The unique order ID"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "search_orders",
        "description": "Search for orders by customer email address",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer email address"
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "get_customer_info",
        "description": "Get customer profile including preferences and order history",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer ID"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "initiate_return",
        "description": "Start the return process for an order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The order ID to return"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the return"
                }
            },
            "required": ["order_id", "reason"]
        }
    },
    {
        "name": "get_policy_info",
        "description": "Get store policy information",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_type": {
                    "type": "string",
                    "enum": ["returns", "shipping", "refunds", "privacy"],
                    "description": "Type of policy to retrieve"
                }
            },
            "required": ["policy_type"]
        }
    },
    {
        "name": "get_recommendations",
        "description": "Get personalized book recommendations",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Customer ID for personalized recommendations"
                },
                "genre": {
                    "type": "string",
                    "description": "Specific genre to recommend from"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of recommendations (default 5)"
                }
            }
        }
    },
    {
        "name": "search_books",
        "description": "Search the book catalog",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (title, author, or keyword)"
                },
                "genre": {
                    "type": "string",
                    "description": "Filter by genre"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_support_ticket",
        "description": "Create a support ticket for human follow-up",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Customer ID if available"
                },
                "issue": {
                    "type": "string",
                    "description": "Description of the issue"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Ticket priority"
                }
            },
            "required": ["issue"]
        }
    }
]
```

### B. Sample Conversation Logs

**Successful Order Tracking**
```
[User] Where's my package?
[Tool Call] search_orders(email="sarah.johnson@email.com")
[Tool Result] [{id: 1, order_number: "ORD-2024-001", status: "shipped"}...]
[Agent] I found 3 orders for your account. Which one are you asking about?
        1. ORD-2024-001 - Shipped (The Great Gatsby)
        2. ORD-2024-002 - Delivered (1984)
        3. ORD-2024-003 - Processing (Dune)

[User] The shipped one
[Tool Call] get_order_status(order_id=1)
[Tool Result] {status: "shipped", tracking: "1Z999AA1...", estimated: "Jan 8"}
[Agent] Your order ORD-2024-001 is on the way! Here are the details:
        - Status: Shipped
        - Tracking: 1Z999AA10123456784
        - Expected delivery: January 8th
```

### C. Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/bookly
JWT_SECRET=your-secure-secret-key

# Optional
CLAUDE_MODEL=claude-sonnet-4-20250514
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-07 | Initial design document |
