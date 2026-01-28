import { create } from 'zustand';
import type { ChatMessage, WebSocketMessage } from '../types';

interface ChatState {
  messages: ChatMessage[];
  isConnected: boolean;
  isTyping: boolean;
  isOpen: boolean;
  sessionId: string | null;
  currentUserEmail: string | null;
  ws: WebSocket | null;
  connect: (userEmail?: string) => void;
  disconnect: () => void;
  sendMessage: (content: string, userEmail?: string) => void;
  toggleChat: () => void;
  openChat: () => void;
  closeChat: () => void;
  clearMessages: () => void;
  resetSession: () => void;
}

// Use proxy in development, or configured URL in production
// In dev mode, Vite proxies /ws to ws://localhost:8000, so use relative URL
function getWebSocketBaseUrl(): string {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  // In development, use relative URL to go through Vite proxy
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
  }
  return 'ws://localhost:8000';
}
const WS_URL = getWebSocketBaseUrl();

function generateSessionId(userEmail?: string): string {
  // Include user identifier in session ID for user-specific sessions
  const userPart = userEmail ? btoa(userEmail).replace(/[^a-zA-Z0-9]/g, '').slice(0, 10) : 'anon';
  return `session-${userPart}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function generateMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isConnected: false,
  isTyping: false,
  isOpen: false,
  sessionId: null,
  currentUserEmail: null,
  ws: null,

  connect: (userEmail?: string) => {
    const { ws, sessionId: existingSessionId, currentUserEmail } = get();

    // If user changed, reset the session
    if (currentUserEmail && userEmail && currentUserEmail !== userEmail) {
      get().resetSession();
    }

    // If already connected with same user, skip
    if (ws?.readyState === WebSocket.OPEN && currentUserEmail === userEmail) return;

    // Close existing connection if user changed
    if (ws && currentUserEmail !== userEmail) {
      ws.close();
    }

    // Generate new session ID if needed, or reuse existing for same user
    const sessionId = (existingSessionId && currentUserEmail === userEmail)
      ? existingSessionId
      : generateSessionId(userEmail);
    
    // Determine WebSocket URL dynamically (use proxy in dev)
    let wsBaseUrl = WS_URL;
    if (!import.meta.env.VITE_WS_URL && typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      wsBaseUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
    }
    const fullWsUrl = `${wsBaseUrl}/ws/chat/${sessionId}`;
    const websocket = new WebSocket(fullWsUrl);

    websocket.onopen = () => {
      set({ isConnected: true, ws: websocket, sessionId, currentUserEmail: userEmail || null });

      // Set user context if email provided
      if (userEmail) {
        websocket.send(JSON.stringify({
          type: 'set_user',
          user_email: userEmail,
        }));
      }
    };

    websocket.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message received:', data.type, data.content?.substring(0, 50));

        switch (data.type) {
          case 'connected':
            // Add welcome message only if no messages exist yet (prevents duplicates on reconnect)
            const currentMessages = get().messages;
            if (currentMessages.length === 0) {
              set({
                messages: [
                  {
                    id: generateMessageId(),
                    role: 'assistant',
                    content: 'Hello! Welcome to Bookly support. How can I help you today?',
                    timestamp: new Date(),
                  },
                ],
              });
            }
            break;

          case 'stream':
            // Handle streaming content - always get fresh state
            const { messages: currentMsgs } = get();
            const lastMsg = currentMsgs[currentMsgs.length - 1];
            
            if (lastMsg?.isStreaming && lastMsg.role === 'assistant') {
              // Append to existing streaming message
              set({
                messages: [
                  ...currentMsgs.slice(0, -1),
                  {
                    ...lastMsg,
                    content: lastMsg.content + (data.content || ''),
                  },
                ],
              });
            } else {
              // Create new streaming message
              set({
                messages: [
                  ...currentMsgs,
                  {
                    id: generateMessageId(),
                    role: 'assistant',
                    content: data.content || '',
                    timestamp: new Date(),
                    isStreaming: true,
                  },
                ],
              });
            }
            break;

          case 'message_complete':
            // Mark message as complete - get fresh state
            const { messages: msgsToUpdate } = get();
            const updatedMsgs = msgsToUpdate.map((msg) =>
              msg.isStreaming ? { ...msg, isStreaming: false } : msg
            );
            set({ messages: updatedMsgs, isTyping: false });
            break;

          case 'typing':
            set({ isTyping: data.status === true });
            break;

          case 'tool_use':
            // Optional: show tool usage indicator
            break;

          case 'error':
            const { messages: errorMsgs } = get();
            set({
              messages: [
                ...errorMsgs,
                {
                  id: generateMessageId(),
                  role: 'assistant',
                  content: data.message || 'An error occurred. Please try again.',
                  timestamp: new Date(),
                },
              ],
              isTyping: false,
            });
            break;
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error, event.data);
      }
    };

    websocket.onclose = () => {
      set({ isConnected: false, ws: null });
    };

    websocket.onerror = () => {
      set({ isConnected: false });
    };

    set({ ws: websocket });
  },

  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null, isConnected: false });
    }
  },

  sendMessage: (content: string, userEmail?: string) => {
    const { ws, messages, isConnected } = get();

    if (!isConnected || !ws || ws.readyState !== WebSocket.OPEN) {
      // Try to connect first
      get().connect(userEmail);
      setTimeout(() => get().sendMessage(content, userEmail), 500);
      return;
    }

    // Add user message to chat
    set({
      messages: [
        ...messages,
        {
          id: generateMessageId(),
          role: 'user',
          content,
          timestamp: new Date(),
        },
      ],
    });

    // Send to server
    ws.send(JSON.stringify({
      type: 'message',
      content,
      user_email: userEmail,
    }));
  },

  toggleChat: () => {
    const { isOpen, isConnected } = get();
    if (!isOpen && !isConnected) {
      get().connect();
    }
    set({ isOpen: !isOpen });
  },

  openChat: () => {
    const { isConnected } = get();
    if (!isConnected) {
      get().connect();
    }
    set({ isOpen: true });
  },

  closeChat: () => set({ isOpen: false }),

  clearMessages: () => set({ messages: [] }),

  resetSession: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
    }
    set({
      messages: [],
      isConnected: false,
      isTyping: false,
      isOpen: false,
      sessionId: null,
      currentUserEmail: null,
      ws: null,
    });
  },
}));
