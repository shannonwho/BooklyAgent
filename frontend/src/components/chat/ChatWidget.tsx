import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Minimize2 } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import clsx from 'clsx';

export default function ChatWidget() {
  const [input, setInput] = useState('');
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    isOpen,
    isTyping,
    isConnected,
    toggleChat,
    closeChat,
    sendMessage,
    connect,
  } = useChatStore();

  const { user, isAuthenticated } = useAuthStore();

  // Auto-scroll to bottom on new messages (within container only)
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Connect with user context when authenticated
  useEffect(() => {
    if (isOpen && !isConnected) {
      connect(isAuthenticated ? user?.email : undefined);
    }
  }, [isOpen, isConnected, isAuthenticated, user?.email, connect]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    sendMessage(input.trim(), isAuthenticated ? user?.email : undefined);
    setInput('');
    inputRef.current?.focus();
  };

  if (!isOpen) {
    return (
      <button
        onClick={toggleChat}
        className="fixed bottom-6 right-6 bg-primary-600 text-white p-4 rounded-full shadow-lg hover:bg-primary-700 transition-all hover:scale-105 z-50"
        aria-label="Open chat"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 animate-fade-in">
      {/* Header */}
      <div className="bg-primary-600 text-white px-4 py-3 rounded-t-2xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <MessageCircle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold">Bookly Support</h3>
            <p className="text-xs text-primary-100">
              {isConnected ? 'Online' : 'Connecting...'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={closeChat}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            aria-label="Minimize chat"
          >
            <Minimize2 className="h-5 w-5" />
          </button>
          <button
            onClick={closeChat}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            aria-label="Close chat"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx(
              'flex animate-fade-in',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={clsx(
                'max-w-[80%] rounded-2xl px-4 py-2',
                message.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-md'
                  : 'bg-gray-100 text-gray-800 rounded-bl-md'
              )}
            >
              <p className="whitespace-pre-wrap text-sm">{message.content}</p>
              {message.isStreaming && (
                <span className="inline-block animate-pulse">...</span>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex space-x-1">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex items-center space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 input text-sm"
            disabled={!isConnected}
          />
          <button
            type="submit"
            disabled={!input.trim() || !isConnected}
            className="btn btn-primary p-2"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        {isAuthenticated && (
          <p className="text-xs text-gray-400 mt-2">
            Logged in as {user?.email}
          </p>
        )}
      </form>
    </div>
  );
}
