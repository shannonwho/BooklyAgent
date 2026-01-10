"""WebSocket endpoint for AI chat support."""
import json
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db, AsyncSessionLocal
from agent.controller import AgentController

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.agents: dict[str, AgentController] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        # Create agent for this session (without db session - will be created per message)
        self.agents[session_id] = AgentController(session_id)

    def disconnect(self, session_id: str):
        """Remove a disconnected client."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.agents:
            del self.agents[session_id]

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


manager = ConnectionManager()


@router.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for chat communication."""
    await manager.connect(websocket, session_id)

    # Send welcome message
    await manager.send_message(session_id, {
        "type": "connected",
        "message": "Connected to Bookly Support",
        "session_id": session_id,
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type", "message")

            if message_type == "message":
                user_message = data.get("content", "")
                user_email = data.get("user_email")  # Optional user context

                if not user_message.strip():
                    continue

                # Get agent for this session
                agent = manager.get_agent(session_id)

                if not agent:
                    # Recreate agent if needed (without db session - will be created per message)
                    agent = AgentController(session_id)
                    manager.agents[session_id] = agent

                # Process message with streaming
                await manager.send_message(session_id, {
                    "type": "typing",
                    "status": True,
                })

                try:
                    # Get database session for agent (create fresh session per message)
                    async with AsyncSessionLocal() as db:
                        agent.db = db

                        # Process message and stream response
                        async for chunk in agent.process_message(
                            user_message,
                            user_email=user_email
                        ):
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

                    # Signal message complete
                    await manager.send_message(session_id, {
                        "type": "message_complete",
                    })

                except Exception as e:
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
                # Update user context
                user_email = data.get("user_email")
                agent = manager.get_agent(session_id)
                if agent:
                    agent.set_user_context(user_email)
                await manager.send_message(session_id, {
                    "type": "user_set",
                    "email": user_email,
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)
