import { useEffect, useRef, useState } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useAuthStore } from '../store/authStore';

export default function SupportPage() {
  const {
    messages,
    isConnected,
    isTyping: isLoading,
    connect,
    disconnect,
    sendMessage,
  } = useChatStore();
  const { user, isAuthenticated } = useAuthStore();
  const [input, setInput] = useState('');
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    connect(isAuthenticated ? user?.email : undefined);
    return () => disconnect();
  }, [connect, disconnect, user?.email]);

  // Auto-scroll within messages container only (not the page)
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    sendMessage(input.trim(), isAuthenticated ? user?.email : undefined);
    setInput('');
  };

  const suggestedQuestions = [
    "Where's my order?",
    "I'd like to return a book",
    "Can you recommend a book?",
    "What's your return policy?",
  ];

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <Bot className="h-6 w-6 text-primary-600" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">Bookly Support</h1>
            <p className="text-sm text-gray-500">
              {isConnected ? (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full" />
                  Online
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full" />
                  Connecting...
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-gray-50">
        {/* Welcome message - show when no user messages have been sent yet */}
        {!messages.some(m => m.role === 'user') && (
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <Bot className="h-8 w-8 text-primary-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Hi{isAuthenticated ? `, ${user?.name?.split(' ')[0]}` : ''}! How can I help you today?
            </h2>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              I can help you with order tracking, returns, book recommendations, and more.
            </p>

            {/* Suggested questions */}
            <div className="flex flex-wrap justify-center gap-2">
              {suggestedQuestions.map((question) => (
                <button
                  key={question}
                  onClick={() => {
                    sendMessage(question, isAuthenticated ? user?.email : undefined);
                  }}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user' ? 'bg-primary-600' : 'bg-gray-200'
              }`}
            >
              {message.role === 'user' ? (
                <User className="h-4 w-4 text-white" />
              ) : (
                <Bot className="h-4 w-4 text-gray-600" />
              )}
            </div>
            <div
              className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.timestamp && (
                <p
                  className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-primary-200' : 'text-gray-400'
                  }`}
                >
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <Bot className="h-4 w-4 text-gray-600" />
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          </div>
        )}

      </div>

      {/* Input */}
      <div className="border-t bg-white px-6 py-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 input"
            disabled={!isConnected || isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || !isConnected || isLoading}
            className="btn btn-primary px-4"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Powered by Claude AI. Your conversation may be used to improve our service.
        </p>
      </div>
    </div>
  );
}
