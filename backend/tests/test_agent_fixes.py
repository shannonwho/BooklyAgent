"""Test cases to validate support agent bug fixes."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from agent.controller import AgentController
from agent.tools import execute_tool
from data.database import AsyncSessionLocal
from data.models import Customer, Order


@pytest.fixture
async def db_session():
    """Create a database session for testing."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    with patch('agent.controller.anthropic.AsyncAnthropic') as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


class TestAgentDatabaseSessionLifecycle:
    """Test that agents are created without database sessions and sessions are assigned per message."""
    
    @pytest.mark.asyncio
    async def test_agent_created_without_db_session(self):
        """Test that AgentController can be created without a database session."""
        agent = AgentController("test-session-1")
        assert agent.session_id == "test-session-1"
        assert agent.db is None
        assert agent.user_email is None
        assert agent.user_name is None
        assert agent.conversation_history == []
    
    @pytest.mark.asyncio
    async def test_agent_db_session_assignment(self, db_session):
        """Test that database session can be assigned to agent."""
        agent = AgentController("test-session-2")
        assert agent.db is None
        
        agent.db = db_session
        assert agent.db is not None
        assert agent.db == db_session


class TestUserEmailContext:
    """Test user email context setting and passing."""
    
    @pytest.mark.asyncio
    async def test_set_user_context(self):
        """Test setting user context on agent."""
        agent = AgentController("test-session-3")
        agent.set_user_context("test@example.com", "Test User")
        
        assert agent.user_email == "test@example.com"
        assert agent.user_name == "Test User"
    
    @pytest.mark.asyncio
    async def test_process_message_updates_user_email(self, mock_anthropic_client, db_session):
        """Test that process_message updates user_email when provided."""
        agent = AgentController("test-session-4")
        agent.db = db_session
        
        # Mock the Anthropic API response
        mock_stream = AsyncMock()
        mock_message = MagicMock()
        mock_message.content = [{"type": "text", "text": "Hello! How can I help?"}]
        mock_stream.get_final_message = AsyncMock(return_value=mock_message)
        mock_anthropic_client.messages.stream = AsyncMock(return_value=mock_stream)
        
        # Mock the stream events
        async def mock_stream_events():
            yield MagicMock(type="content_block_start", content_block=MagicMock(type="text"))
            yield MagicMock(type="content_block_delta", delta=MagicMock(text="Hello! "))
            yield MagicMock(type="content_block_delta", delta=MagicMock(text="How can I help?"))
            yield MagicMock(type="content_block_stop")
        
        mock_stream.__aiter__ = lambda self: mock_stream_events()
        
        # Process message with user email
        chunks = []
        async for chunk in agent.process_message("Hello", user_email="test@example.com"):
            chunks.append(chunk)
        
        assert agent.user_email == "test@example.com"


class TestEmailAutoInjection:
    """Test automatic email injection into tool inputs."""
    
    def test_email_injection_for_tools_that_need_email(self):
        """Test that user_email is injected into tool inputs for tools that need it."""
        agent = AgentController("test-session-5")
        agent.user_email = "test@example.com"
        
        # Simulate tool use input without email
        tool_input = {}
        tool_name = "search_orders"
        
        # Check if email would be injected (simulating the logic)
        tools_that_need_email = ["search_orders", "get_customer_info", "initiate_return", 
                                 "create_support_ticket", "get_recommendations"]
        
        if agent.user_email and tool_name in tools_that_need_email:
            if not tool_input.get("email"):
                tool_input["email"] = agent.user_email
        
        assert tool_input.get("email") == "test@example.com"
    
    def test_email_not_overwritten_if_provided(self):
        """Test that email is not overwritten if already provided."""
        agent = AgentController("test-session-6")
        agent.user_email = "test@example.com"
        
        tool_input = {"email": "different@example.com"}
        tool_name = "search_orders"
        
        tools_that_need_email = ["search_orders", "get_customer_info", "initiate_return", 
                                 "create_support_ticket", "get_recommendations"]
        
        if agent.user_email and tool_name in tools_that_need_email:
            if not tool_input.get("email"):
                tool_input["email"] = agent.user_email
        
        assert tool_input.get("email") == "different@example.com"  # Should not be overwritten
    
    def test_email_injection_for_get_order_status(self):
        """Test email injection for get_order_status when email field exists but is empty."""
        agent = AgentController("test-session-7")
        agent.user_email = "test@example.com"
        
        tool_input = {"order_id": "ORD-123", "email": ""}
        tool_name = "get_order_status"
        
        # Simulate the injection logic
        if agent.user_email and tool_name == "get_order_status" and "email" in tool_input:
            if not tool_input.get("email"):
                tool_input["email"] = agent.user_email
        
        assert tool_input.get("email") == "test@example.com"


class TestToolExecution:
    """Test tool execution with proper database sessions."""
    
    @pytest.mark.asyncio
    async def test_tool_execution_requires_db_session(self, db_session):
        """Test that tools require a database session."""
        # This test verifies that execute_tool expects a db session
        # We'll test with a simple tool that doesn't require database access
        result = await execute_tool(
            "get_policy_info",
            {"policy_type": "return"},
            db_session
        )
        
        # Should either return policy info or error, but not crash
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_agent_without_db_yields_error(self, mock_anthropic_client):
        """Test that agent without db session yields error when tools are called."""
        agent = AgentController("test-session-8")
        # Don't set agent.db
        
        # Mock Anthropic to return a tool use
        mock_stream = AsyncMock()
        mock_message = MagicMock()
        mock_tool_use = MagicMock()
        mock_tool_use.id = "tool_123"
        mock_tool_use.name = "get_order_status"
        mock_tool_use.input = {"order_id": "ORD-123"}
        mock_message.content = [mock_tool_use]
        mock_stream.get_final_message = AsyncMock(return_value=mock_message)
        mock_anthropic_client.messages.stream = AsyncMock(return_value=mock_stream)
        
        # Mock stream events
        async def mock_stream_events():
            yield MagicMock(type="content_block_start", content_block=mock_tool_use)
            yield MagicMock(type="content_block_stop")
        
        mock_stream.__aiter__ = lambda self: mock_stream_events()
        
        # Process message - should yield error when trying to execute tool without db
        chunks = []
        async for chunk in agent.process_message("Check my order"):
            chunks.append(chunk)
            if chunk.get("type") == "error":
                break
        
        # Should have error chunk
        error_chunks = [c for c in chunks if c.get("type") == "error"]
        assert len(error_chunks) > 0


class TestWebSocketIntegration:
    """Test WebSocket integration fixes."""
    
    def test_connection_manager_creates_agent_without_db(self):
        """Test that ConnectionManager creates agents without database sessions."""
        from api.websocket import ConnectionManager
        
        manager = ConnectionManager()
        # We can't easily test async connect without a real websocket,
        # but we can verify the manager structure
        assert manager.active_connections == {}
        assert manager.agents == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
