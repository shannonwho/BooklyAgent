"""Session management for chat conversations."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class ConversationPhase(Enum):
    """Tracks where we are in the conversation flow."""
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    PROCESSING = "processing"
    CONFIRMATION = "confirmation"
    RESOLUTION = "resolution"
    ESCALATION = "escalation"


class IntentType(Enum):
    """Customer's primary intent."""
    ORDER_STATUS = "order_status"
    RETURN_REQUEST = "return_request"
    REFUND_INQUIRY = "refund_inquiry"
    PRODUCT_SEARCH = "product_search"
    RECOMMENDATION = "recommendation"
    POLICY_QUESTION = "policy_question"
    ACCOUNT_ISSUE = "account_issue"
    COMPLAINT = "complaint"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"


@dataclass
class Message:
    """Individual message in conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[Dict]] = None
    tool_results: Optional[List[Dict]] = None


@dataclass
class GatheredInfo:
    """Information collected during conversation."""
    customer_email: Optional[str] = None
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None

    # For returns/refunds
    return_items: List[Dict] = field(default_factory=list)
    return_reason: Optional[str] = None

    # For product search
    search_query: Optional[str] = None
    preferred_genres: List[str] = field(default_factory=list)

    # Metadata
    verified_identity: bool = False
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None


@dataclass
class ConversationState:
    """Complete state of a conversation session."""
    session_id: str
    customer_id: Optional[str] = None

    # Conversation tracking
    messages: List[Message] = field(default_factory=list)
    current_phase: ConversationPhase = ConversationPhase.GREETING
    detected_intent: IntentType = IntentType.UNKNOWN

    # Information gathering
    gathered_info: GatheredInfo = field(default_factory=GatheredInfo)
    pending_questions: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Sentiment and escalation tracking
    customer_sentiment: str = "neutral"  # "positive", "neutral", "negative", "angry"
    frustration_indicators: int = 0  # Count of negative sentiment

    # Rate limiting
    message_count: int = 0
    tool_call_count: int = 0


class SessionManager:
    """Manages conversation sessions."""

    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}

    def create_session(self, session_id: str) -> ConversationState:
        """Create new conversation session."""
        state = ConversationState(session_id=session_id)
        self.sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Retrieve existing session."""
        return self.sessions.get(session_id)

    def get_or_create_session(self, session_id: str) -> ConversationState:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]

    def update_session(self, session_id: str, state: ConversationState):
        """Update session state."""
        state.updated_at = datetime.utcnow()
        self.sessions[session_id] = state

    def add_message(self, session_id: str, message: Message):
        """Add message to session history."""
        if session_id in self.sessions:
            self.sessions[session_id].messages.append(message)
            self.sessions[session_id].message_count += 1
            self.sessions[session_id].updated_at = datetime.utcnow()

    def get_conversation_history(
        self,
        session_id: str,
        last_n: int = 10
    ) -> List[Message]:
        """Get recent conversation history."""
        if session_id in self.sessions:
            return self.sessions[session_id].messages[-last_n:]
        return []

    def should_escalate(self, session_id: str) -> bool:
        """Determine if conversation should be escalated."""
        if session_id not in self.sessions:
            return False

        state = self.sessions[session_id]

        # Escalation criteria
        if state.gathered_info.requires_escalation:
            return True
        if state.frustration_indicators >= 3:
            return True
        if state.current_phase == ConversationPhase.ESCALATION:
            return True
        if state.message_count > 20:  # Very long conversation
            return True

        return False

    def set_customer_context(
        self,
        session_id: str,
        email: str,
        name: Optional[str] = None
    ):
        """Set customer context for a session."""
        if session_id in self.sessions:
            state = self.sessions[session_id]
            state.gathered_info.customer_email = email
            state.gathered_info.customer_name = name
            state.gathered_info.verified_identity = True

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove old inactive sessions."""
        now = datetime.utcnow()
        to_remove = [
            sid for sid, state in self.sessions.items()
            if (now - state.updated_at).total_seconds() > max_age_hours * 3600
        ]
        for sid in to_remove:
            del self.sessions[sid]

    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
