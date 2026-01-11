# Bookly Support Agent - Design Methodology

This document explains the methodology and design behind how the Bookly support agent handles key interaction scenarios.

---

## 1. Multi-Turn Interaction (Collecting Information Before Responding)

### Design Pattern: **Agentic Loop with Conversation History**

**Implementation** (`controller.py:44-47`, `controller.py:102-105`):
```python
# Conversation history is maintained across turns
self.conversation_history.append({
    "role": "user",
    "content": user_message
})
# ... after response ...
self.conversation_history.append({
    "role": "assistant",
    "content": assistant_content
})
```

**System Prompt Guidance** (`prompts.py:48-52`):
```
### Multi-turn Interactions
- Maintain context from previous messages in the conversation
- Reference earlier parts of the conversation naturally
- Don't ask for information the customer already provided
- Keep track of partial information and what's still needed
```

### Example Flow: Return Request
1. **User**: "I want to return my order"
2. **Agent**: Uses `search_orders` tool → finds multiple orders → asks "Which order?"
3. **User**: "The one from last week"
4. **Agent**: Identifies order, asks "What's the reason for return?"
5. **User**: "It was damaged"
6. **Agent**: Confirms details, then uses `initiate_return` tool

The agent accumulates information across turns before taking the final action.

---

## 2. Agent Taking an Action / Using a Tool

### Design Pattern: **Tool Use with Agentic Loop**

**Tool Definitions** (`tools.py:14-170`): 8 tools available:

| Tool | Action Type |
|------|-------------|
| `get_order_status` | Read data |
| `search_orders` | Read data |
| `get_customer_info` | Read data |
| `initiate_return` | **Write action** (modifies database) |
| `get_policy_info` | Read data |
| `get_recommendations` | Read data |
| `search_books` | Read data |
| `create_support_ticket` | **Write action** (creates ticket) |

**Execution Loop** (`controller.py:58-180`):
```python
while turn_count < self.max_turns:
    # Call Claude API with tools
    async with self.client.messages.stream(..., tools=TOOLS, ...):
        # Stream response and detect tool_use blocks

    # If tool_use detected:
    tool_uses = [block for block in content if block.type == "tool_use"]

    if tool_uses:
        for tool_use in tool_uses:
            result = await execute_tool(tool_use.name, tool_input, self.db)
            # Add result back to conversation
        # Loop continues for Claude to process tool results
```

### Example: "Where's my order?"
1. Claude decides to call `search_orders` with user's email
2. Tool executes database query, returns order list
3. Result added to conversation as `tool_result`
4. Claude processes result and responds with order details

**Safety for Sensitive Actions** (`prompts.py:14-18`):
```
2. **ASK BEFORE ACTING**: For sensitive actions (returns, refunds, account changes):
   - Gather ALL required information first
   - Confirm the action with the customer
   - Verify their identity (email/order ID)
```

---

## 3. Agent Asks Clarifying Question Instead of Answering

### Design Pattern: **Prompt-Driven Clarification Behavior**

**System Prompt Instructions** (`prompts.py:54-61`):
```
### When to Ask Clarifying Questions
Ask clarifying questions when:
- The customer's request is ambiguous
- Multiple orders/items could match their description
- You need to confirm before taking an action
- The customer's intent is unclear

Example: "I see you have two recent orders. Which one would you like
to check on - the order from January 3rd or January 5th?"
```

**Handling Ambiguity** (`prompts.py:108-109`):
```
### Ambiguous Queries
"Just to make sure I help you with the right thing, are you asking
about [option A] or [option B]?"
```

### Example Scenarios:

| User Input | Why Clarification Needed | Agent Response |
|------------|--------------------------|----------------|
| "Check my order" | Multiple orders exist | "I found 3 orders. Which one - ORD-001 (Jan 3), ORD-002 (Jan 5), or ORD-003 (Jan 8)?" |
| "I want a refund" | No order specified | "I'd be happy to help with a refund. Could you provide the order number or email so I can look it up?" |
| "Return this" | Unclear what "this" refers to | "To process a return, I'll need to know which order you'd like to return. Can you share the order number?" |

**Context-Aware Clarification** (`prompts.py:130-143`):
```python
def get_system_prompt(user_email=None, user_name=None):
    if context_parts:
        context = "\n".join(context_parts)
    else:
        context = "Customer is not logged in. Ask for email when needed..."
```

When user is not logged in, the agent knows to ask for email before attempting order lookups.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    User Message                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentController.process_message()               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  conversation_history (maintains multi-turn context)  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Claude API (with tools)                      │
│  • System prompt guides when to ask vs. act                 │
│  • Decides: respond / use tool / ask clarifying question    │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     ┌────────┐  ┌────────┐  ┌────────────┐
     │ Text   │  │ Tool   │  │ Clarifying │
     │Response│  │  Use   │  │  Question  │
     └────────┘  └───┬────┘  └────────────┘
                     │
                     ▼
              ┌─────────────┐
              │execute_tool │ ──▶ Database
              └─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │Tool Result  │ ──▶ Back to Claude
              └─────────────┘     for final response
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/agent/controller.py` | Main agent loop, conversation history, tool execution |
| `backend/agent/prompts.py` | System prompt with behavior guidelines |
| `backend/agent/tools.py` | Tool definitions and database operations |
| `backend/api/websocket.py` | WebSocket handler connecting frontend to agent |
| `frontend/src/store/chatStore.ts` | Frontend state management for chat |
