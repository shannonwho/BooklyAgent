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
    const { ws, sessionId: existingSessionId, currentUserEmail, isConnected } = get();

    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:43',message:'connect called',data:{userEmail,existingSessionId,currentUserEmail,wsReadyState:ws?.readyState,wsReadyStateName:ws?.readyState===WebSocket.OPEN?'OPEN':ws?.readyState===WebSocket.CONNECTING?'CONNECTING':ws?.readyState===WebSocket.CLOSING?'CLOSING':ws?.readyState===WebSocket.CLOSED?'CLOSED':'UNKNOWN',isConnected,wsUrl:WS_URL},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion

    // If user changed, reset the session
    if (currentUserEmail && userEmail && currentUserEmail !== userEmail) {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:50',message:'User changed, resetting session',data:{oldEmail:currentUserEmail,newEmail:userEmail},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      get().resetSession();
    }

    // If already connected with same user, skip
    if (ws?.readyState === WebSocket.OPEN && currentUserEmail === userEmail) {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:56',message:'Already connected, skipping',data:{userEmail,currentUserEmail,readyState:ws.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
      return;
    }

    // Close existing connection if user changed
    if (ws && currentUserEmail !== userEmail) {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:59',message:'Closing existing connection due to user change',data:{oldEmail:currentUserEmail,newEmail:userEmail,readyState:ws.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
      // #endregion
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

    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:85',message:'WebSocket created',data:{sessionId,wsUrl:fullWsUrl,wsBaseUrl,originalWS_URL:WS_URL,hasViteWsUrl:!!import.meta.env.VITE_WS_URL,windowHost:typeof window !== 'undefined' ? window.location.host : 'N/A',windowHostname:typeof window !== 'undefined' ? window.location.hostname : 'N/A',initialReadyState:websocket.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A'})}).catch(()=>{});
    // #endregion

    websocket.onopen = () => {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:73',message:'WebSocket onopen fired',data:{sessionId,readyState:websocket.readyState,userEmail},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      set({ isConnected: true, ws: websocket, sessionId, currentUserEmail: userEmail || null });
      
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:77',message:'State updated after onopen',data:{sessionId,isConnected:true,userEmail},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion

      // Set user context if email provided
      if (userEmail) {
        // #region agent log
        fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:80',message:'Sending set_user message',data:{userEmail},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        websocket.send(JSON.stringify({
          type: 'set_user',
          user_email: userEmail,
        }));
      }
    };

    websocket.onmessage = (event) => {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:88',message:'WebSocket message received',data:{rawData:event.data,dataLength:event.data?.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
      // #endregion
      const data: WebSocketMessage = JSON.parse(event.data);
      const { messages } = get();

      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:92',message:'Parsed WebSocket message',data:{type:data.type,hasContent:!!data.content,hasMessage:!!data.message,contentPreview:data.content?.substring(0,50)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
      // #endregion

      switch (data.type) {
        case 'connected':
          // #region agent log
          fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:99',message:'Received connected message',data:{sessionId,messageCount:messages.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
          // #endregion
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

    websocket.onclose = (event) => {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:180',message:'WebSocket onclose fired',data:{sessionId,code:event.code,reason:event.reason,wasClean:event.wasClean,readyState:websocket.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
      set({ isConnected: false, ws: null });
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:182',message:'State updated after onclose',data:{sessionId,isConnected:false},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion
    };

    websocket.onerror = (error) => {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:184',message:'WebSocket onerror fired',data:{sessionId,readyState:websocket.readyState,errorType:error?.type,wsUrl:`${WS_URL}/ws/chat/${sessionId}`},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
      // #endregion
      set({ isConnected: false });
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:186',message:'State updated after onerror',data:{sessionId,isConnected:false},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion
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

    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:181',message:'sendMessage called',data:{content,userEmail,isConnected,wsExists:!!ws,wsReadyState:ws?.readyState,wsReadyStateName:ws?.readyState===WebSocket.OPEN?'OPEN':ws?.readyState===WebSocket.CONNECTING?'CONNECTING':ws?.readyState===WebSocket.CLOSING?'CLOSING':ws?.readyState===WebSocket.CLOSED?'CLOSED':'UNKNOWN'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion

    if (!isConnected || !ws || ws.readyState !== WebSocket.OPEN) {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:184',message:'Not connected or not ready, attempting reconnect',data:{isConnected,wsExists:!!ws,wsReadyState:ws?.readyState,wsReadyStateName:ws?.readyState===WebSocket.OPEN?'OPEN':ws?.readyState===WebSocket.CONNECTING?'CONNECTING':ws?.readyState===WebSocket.CLOSING?'CLOSING':ws?.readyState===WebSocket.CLOSED?'CLOSED':'UNKNOWN'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
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

    // #region agent log
    const messagePayload = {type: 'message', content, user_email: userEmail};
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chatStore.ts:205',message:'Sending message to WebSocket',data:{payload:messagePayload,wsReadyState:ws.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion

    // Send to server
    ws.send(JSON.stringify(messagePayload));
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
