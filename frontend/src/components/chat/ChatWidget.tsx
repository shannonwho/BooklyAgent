import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Minimize2, Star } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import { analyticsApi } from '../../services/analytics';
import clsx from 'clsx';

export default function ChatWidget() {
  const [input, setInput] = useState('');
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');
  const [submittingRating, setSubmittingRating] = useState(false);
  const [ratingSubmitted, setRatingSubmitted] = useState(false);
  const [ratingError, setRatingError] = useState<string | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    isOpen,
    isTyping,
    isConnected,
    sessionId,
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

  // Connect with user context when authenticated or reconnect when user changes
  useEffect(() => {
    if (isOpen) {
      connect(isAuthenticated ? user?.email : undefined);
    }
  }, [isOpen, isAuthenticated, user?.email, connect]);

  // Show rating only when chat is closed (user wraps up conversation)
  useEffect(() => {
    const hasConversation = messages.some(m => m.role === 'user');
    const ratingKey = sessionId ? `rating_submitted_${sessionId}` : null;
    const ratingAlreadyShown = ratingKey ? sessionStorage.getItem(ratingKey) : false;
    
    // Show rating when chat is closed if there was a conversation and rating hasn't been shown
    if (!isOpen && hasConversation && !ratingAlreadyShown && sessionId) {
      // Only show if we haven't already shown it for this close event
      if (!showRating) {
        setShowRating(true);
      }
    } else if (isOpen) {
      // Don't hide rating when reopening - let user complete it if they want
      // Rating will be hidden when submitted or dismissed
    }
  }, [isOpen, messages, showRating, sessionId]);

  const handleRatingSubmit = async () => {
    if (!rating || !sessionId || submittingRating) return;
    
    // Clear any previous errors
    setRatingError(null);
    setSubmittingRating(true);
    
    try {
      await analyticsApi.submitRating(sessionId, rating, ratingComment || undefined);
      // Mark rating as submitted to prevent showing again
      const ratingKey = `rating_submitted_${sessionId}`;
      sessionStorage.setItem(ratingKey, 'true');
      
      // Show success state briefly before hiding
      setRatingSubmitted(true);
      
      // Hide rating widget after a short delay to show success message
      setTimeout(() => {
        setShowRating(false);
        setRatingSubmitted(false);
        setRating(0);
        setRatingComment('');
        setSubmittingRating(false);
        setRatingError(null);
      }, 1500);
    } catch (error: any) {
      console.error('Failed to submit rating:', error);
      setSubmittingRating(false);
      
      // Extract error message
      const errorMessage = error?.response?.data?.detail 
        || error?.response?.data?.message 
        || error?.message 
        || 'Failed to submit rating. Please try again.';
      
      setRatingError(errorMessage);
    }
  };

  const handleRatingDismiss = () => {
    // Mark rating as dismissed to prevent showing again
    if (sessionId) {
      const ratingKey = `rating_submitted_${sessionId}`;
      sessionStorage.setItem(ratingKey, 'dismissed');
    }
    setShowRating(false);
    setRatingError(null);
    setRating(0);
    setRatingComment('');
  };

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

      {/* Rating Widget - shown when chat is closed */}
      {showRating && !isOpen && (
        <div className="fixed bottom-6 right-6 w-96 bg-white rounded-2xl shadow-2xl p-4 z-50 animate-fade-in border-2 border-primary-200">
          <div className={clsx(
            "rounded-xl px-4 py-3 transition-colors",
            ratingSubmitted 
              ? "bg-green-50 border border-green-200" 
              : ratingError
              ? "bg-red-50 border border-red-200"
              : "bg-blue-50 border border-blue-200"
          )}>
            {ratingSubmitted ? (
              <div className="text-center py-2">
                <p className="text-sm font-medium text-green-700 mb-1">
                  ✓ Thank you for your feedback!
                </p>
                <p className="text-xs text-green-600">
                  Your rating has been submitted successfully.
                </p>
              </div>
            ) : (
              <>
                <p className="text-sm font-medium text-gray-900 mb-2">How was your experience?</p>
                {ratingError && (
                  <div className="mb-2 p-2 bg-red-100 border border-red-300 rounded-md">
                    <p className="text-xs text-red-700">{ratingError}</p>
                  </div>
                )}
                <div className="flex items-center space-x-1 mb-3">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => {
                        setRating(star);
                        setRatingError(null); // Clear error when user selects a rating
                      }}
                      disabled={submittingRating}
                      className="focus:outline-none disabled:opacity-50"
                      aria-label={`Rate ${star} stars`}
                    >
                      <Star
                        className={clsx(
                          'h-6 w-6 transition-colors',
                          star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                        )}
                      />
                    </button>
                  ))}
                </div>
                <textarea
                  value={ratingComment}
                  onChange={(e) => {
                    setRatingComment(e.target.value);
                    setRatingError(null); // Clear error when user types
                  }}
                  placeholder="Optional feedback..."
                  disabled={submittingRating}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 mb-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  rows={2}
                />
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleRatingSubmit}
                    disabled={!rating || submittingRating}
                    className="text-xs bg-primary-600 text-white px-3 py-1 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {submittingRating ? 'Submitting...' : 'Submit'}
                  </button>
                  <button
                    onClick={handleRatingDismiss}
                    disabled={submittingRating}
                    className="text-xs text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Dismiss
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

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
