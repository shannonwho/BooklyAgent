"""WebSocket endpoint for AI chat support."""
import json
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db, AsyncSessionLocal
from agent.controller import AgentController
from analytics.event_collector import track_conversation_end, track_event

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections with user-specific sessions."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.agents: dict[str, AgentController] = {}
        self.session_users: dict[str, Optional[str]] = {}  # Track user email per session

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        # Create agent for this session (without db session - will be created per message)
        self.agents[session_id] = AgentController(session_id)
        self.session_users[session_id] = None
        
        # Track chat widget opened
        try:
            async with AsyncSessionLocal() as db:
                await track_event(
                    db,
                    event_type="chat_widget_opened",
                    session_id=session_id,
                    user_email=self.session_users.get(session_id)
                )
        except Exception:
            pass  # Don't fail connection if tracking fails

    async def disconnect(self, session_id: str):
        """Remove a disconnected client."""
        # Track conversation end before cleanup
        try:
            async with AsyncSessionLocal() as db:
                agent = self.agents.get(session_id)
                escalated = False
                if agent and agent.turn_count > 0:
                    # Check if any support tickets were created (escalation indicator)
                    # This is a simplified check - in production you'd query the database
                    # Check tools_used from conversation history
                    tools_used = getattr(agent, 'tools_used', [])
                    if isinstance(tools_used, list):
                        escalated = "create_support_ticket" in tools_used
                    elif hasattr(agent, 'conversation_history'):
                        # Fallback: check conversation history for ticket creation
                        history = agent.conversation_history or []
                        escalated = any(
                            isinstance(msg, dict) and msg.get("role") == "assistant" 
                            and "create_support_ticket" in str(msg.get("content", ""))
                            for msg in history
                        )
                
                await track_conversation_end(
                    db,
                    session_id,
                    resolved=not escalated,
                    escalated=escalated
                )
        except Exception:
            pass  # Don't fail disconnect if tracking fails
        
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.agents:
            del self.agents[session_id]
        if session_id in self.session_users:
            del self.session_users[session_id]

    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific client."""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def send_stream(self, session_id: str, content: str):
        """Send streaming content to a client."""
        await self.send_message(session_id, {
            "type": "stream",
            "content": content,
        })

    def get_agent(self, session_id: str) -> Optional[AgentController]:
        """Get the agent for a session."""
        return self.agents.get(session_id)

    def set_session_user(self, session_id: str, user_email: Optional[str]):
        """Set or update the user for a session. Resets agent if user changed."""
        current_user = self.session_users.get(session_id)

        # If user changed, reset the agent's conversation
        if current_user is not None and user_email != current_user:
            if session_id in self.agents:
                self.agents[session_id].reset_conversation()

        self.session_users[session_id] = user_email
        if session_id in self.agents:
            self.agents[session_id].set_user_context(user_email)

    def get_session_user(self, session_id: str) -> Optional[str]:
        """Get the user email for a session."""
        return self.session_users.get(session_id)


manager = ConnectionManager()


@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for chat communication."""
    # #region agent log
    try:
        import json
        import os
        log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps({"location":"websocket.py:78","message":"WebSocket endpoint called","data":{"session_id":session_id},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"})+'\n')
    except Exception:
        pass
    # #endregion
    await manager.connect(websocket, session_id)

    # #region agent log
    try:
        import json
        import os
        log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps({"location":"websocket.py:84","message":"WebSocket connected","data":{"session_id":session_id},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"})+'\n')
    except Exception:
        pass
    # #endregion

    # Send welcome message
    await manager.send_message(session_id, {
        "type": "connected",
        "message": "Connected to Bookly Support",
        "session_id": session_id,
    })

    try:
        while True:
            # Receive message from client
            # #region agent log
            try:
                import os
                log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"location":"websocket.py:96","message":"Waiting for WebSocket message","data":{"session_id":session_id},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"})+'\n')
            except Exception:
                pass
            # #endregion
            data = await websocket.receive_json()
            message_type = data.get("type", "message")
            # #region agent log
            try:
                import os
                log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, 'a') as f:
                    f.write(json.dumps({"location":"websocket.py:99","message":"WebSocket message received","data":{"session_id":session_id,"message_type":message_type,"has_content":bool(data.get("content")),"content_preview":str(data.get("content",""))[:50]},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"})+'\n')
            except Exception:
                pass
            # #endregion

            if message_type == "message":
                user_message = data.get("content", "")
                user_email = data.get("user_email")  # Optional user context

                # #region agent log
                try:
                    import os
                    log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({"location":"websocket.py:100","message":"Processing message type","data":{"session_id":session_id,"user_message":user_message[:100],"user_email":user_email,"message_length":len(user_message)},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"})+'\n')
                except Exception:
                    pass
                # #endregion

                if not user_message.strip():
                    continue

                # Update session user (will reset conversation if user changed)
                if user_email:
                    manager.set_session_user(session_id, user_email)

                # Get agent for this session
                agent = manager.get_agent(session_id)

                if not agent:
                    # Recreate agent if needed (without db session - will be created per message)
                    agent = AgentController(session_id)
                    manager.agents[session_id] = agent
                    if user_email:
                        agent.set_user_context(user_email)

                # #region agent log
                try:
                    import os
                    log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, 'a') as f:
                        f.write(json.dumps({"location":"websocket.py:120","message":"Starting message processing","data":{"session_id":session_id,"has_agent":bool(agent),"user_email":user_email},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})+'\n')
                except Exception:
                    pass
                # #endregion

                # Process message with streaming
                await manager.send_message(session_id, {
                    "type": "typing",
                    "status": True,
                })

                try:
                    # Get database session for agent (create fresh session per message)
                    async with AsyncSessionLocal() as db:
                        agent.db = db

                        # #region agent log
                        try:
                            import os
                            log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                            os.makedirs(os.path.dirname(log_path), exist_ok=True)
                            with open(log_path, 'a') as f:
                                f.write(json.dumps({"location":"websocket.py:132","message":"Calling agent.process_message","data":{"session_id":session_id,"user_message_length":len(user_message)},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})+'\n')
                        except Exception:
                            pass
                        # #endregion

                        # Process message and stream response
                        chunk_count = 0
                        async for chunk in agent.process_message(
                            user_message,
                            user_email=user_email
                        ):
                            chunk_count += 1
                            # #region agent log
                            try:
                                import os
                                log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                                with open(log_path, 'a') as f:
                                    f.write(json.dumps({"location":"websocket.py:137","message":"Received chunk from agent","data":{"session_id":session_id,"chunk_type":chunk.get("type"),"chunk_count":chunk_count,"has_content":bool(chunk.get("content"))},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})+'\n')
                            except Exception:
                                pass
                            # #endregion
                            if chunk["type"] == "content":
                                await manager.send_stream(session_id, chunk["content"])
                            elif chunk["type"] == "tool_use":
                                await manager.send_message(session_id, {
                                    "type": "tool_use",
                                    "tool": chunk["tool"],
                                    "status": "executing",
                                })
                            elif chunk["type"] == "tool_result":
                                await manager.send_message(session_id, {
                                    "type": "tool_result",
                                    "tool": chunk["tool"],
                                    "status": "complete",
                                })

                        # #region agent log
                        try:
                            import os
                            log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                            os.makedirs(os.path.dirname(log_path), exist_ok=True)
                            with open(log_path, 'a') as f:
                                f.write(json.dumps({"location":"websocket.py:155","message":"Finished processing chunks","data":{"session_id":session_id,"total_chunks":chunk_count},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})+'\n')
                        except Exception:
                            pass
                        # #endregion

                    # Signal message complete
                    await manager.send_message(session_id, {
                        "type": "message_complete",
                    })

                except Exception as e:
                    # #region agent log
                    try:
                        import os
                        log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, 'a') as f:
                            f.write(json.dumps({"location":"websocket.py:156","message":"Error processing message","data":{"session_id":session_id,"error":str(e),"error_type":type(e).__name__},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})+'\n')
                    except Exception:
                        pass
                    # #endregion
                    print(f"Error processing message: {e}")
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": "I apologize, but I encountered an error processing your request. Please try again.",
                    })

                finally:
                    await manager.send_message(session_id, {
                        "type": "typing",
                        "status": False,
                    })

            elif message_type == "ping":
                await manager.send_message(session_id, {"type": "pong"})

            elif message_type == "set_user":
                # Update user context (will reset conversation if user changed)
                user_email = data.get("user_email")
                manager.set_session_user(session_id, user_email)
                await manager.send_message(session_id, {
                    "type": "user_set",
                    "email": user_email,
                })

    except WebSocketDisconnect:
        await manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(session_id)
