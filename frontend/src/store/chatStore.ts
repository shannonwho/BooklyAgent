import { create } from 'zustand';
import type { ChatMessage, WebSocketMessage } from '../types';

interface ChatState {
  messages: ChatMessage[];
  isConnected: boolean;
  isTyping: boolean;
  isOpen: boolean;
  sessionId: string | null;
  ws: WebSocket | null;
  connect: (userEmail?: string) => void;
  disconnect: () => void;
  sendMessage: (content: string, userEmail?: string) => void;
  toggleChat: () => void;
  openChat: () => void;
  closeChat: () => void;
  clearMessages: () => void;
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
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
  ws: null,

  connect: (userEmail?: string) => {
    const { ws, sessionId: existingSessionId } = get();
    if (ws?.readyState === WebSocket.OPEN) return;

    const sessionId = existingSessionId || generateSessionId();
    const websocket = new WebSocket(`${WS_URL}/ws/chat/${sessionId}`);

    websocket.onopen = () => {
      set({ isConnected: true, sessionId });

      // Set user context if email provided
      if (userEmail) {
        websocket.send(JSON.stringify({
          type: 'set_user',
          user_email: userEmail,
        }));
      }
    };

    websocket.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);
      const { messages } = get();

      switch (data.type) {
        case 'connected':
          // Add welcome message only if no messages exist yet (prevents duplicates on reconnect)
          if (messages.length === 0) {
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
          // Handle streaming content
          const lastMessage = messages[messages.length - 1];
          if (lastMessage?.isStreaming && lastMessage.role === 'assistant') {
            // Append to existing streaming message
            set({
              messages: [
                ...messages.slice(0, -1),
                {
                  ...lastMessage,
                  content: lastMessage.content + (data.content || ''),
                },
              ],
            });
          } else {
            // Create new streaming message
            set({
              messages: [
                ...messages,
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
          // Mark message as complete
          const updatedMessages = messages.map((msg) =>
            msg.isStreaming ? { ...msg, isStreaming: false } : msg
          );
          set({ messages: updatedMessages, isTyping: false });
          break;

        case 'typing':
          set({ isTyping: data.status === true });
          break;

        case 'tool_use':
          // Optional: show tool usage indicator
          break;

        case 'error':
          set({
            messages: [
              ...messages,
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

    if (!isConnected || !ws) {
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
}));
