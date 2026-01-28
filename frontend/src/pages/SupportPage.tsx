import { useEffect, useRef, useState } from 'react';
import { Send, Bot, User, Loader2, Star } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useAuthStore } from '../store/authStore';
import { analyticsApi } from '../services/analytics';
import clsx from 'clsx';

export default function SupportPage() {
  const {
    messages,
    isConnected,
    isTyping: isLoading,
    sessionId,
    connect,
    sendMessage,
  } = useChatStore();
  const { user, isAuthenticated } = useAuthStore();
  const [input, setInput] = useState('');
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');
  const [submittingRating, setSubmittingRating] = useState(false);
  const [ratingSubmitted, setRatingSubmitted] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Connect when component mounts or user changes
    // Don't disconnect on unmount - let the connection persist across navigation
    // The ChatWidget also uses the same connection, so we shouldn't close it
    connect(isAuthenticated ? user?.email : undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user?.email]);

  // Show rating when conversation ends (after inactivity period)
  useEffect(() => {
    const hasConversation = messages.some(m => m.role === 'user');
    const lastMessage = messages[messages.length - 1];
    const conversationEnded = !isLoading && hasConversation && lastMessage && !lastMessage.isStreaming;
    
    // Check if rating was already submitted/dismissed
    const ratingKey = sessionId ? `rating_submitted_${sessionId}` : null;
    const ratingAlreadyShown = ratingKey ? sessionStorage.getItem(ratingKey) : false;
    
    // Hide rating if conversation continues (user sends new message while rating is shown)
    if (isLoading && showRating) {
      setShowRating(false);
      return;
    }
    
    // Show rating if conversation ended and we haven't shown it yet
    if (conversationEnded && !showRating && !ratingAlreadyShown && hasConversation) {
      // Wait 3 seconds after conversation ends before showing rating
      const timer = setTimeout(() => {
        setShowRating(true);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [messages, isLoading, showRating, sessionId]);

  // Auto-scroll within messages container only (not the page)
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SupportPage.tsx:34',message:'Rendering connection status',data:{isConnected},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
  }, [isConnected]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SupportPage.tsx:36',message:'handleSubmit called',data:{input,inputTrimmed:input.trim(),isLoading,isConnected},"timestamp":Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    if (!input.trim() || isLoading) {
      // #region agent log
      fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SupportPage.tsx:38',message:'handleSubmit early return',data:{inputTrimmed:input.trim(),isLoading},"timestamp":Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion
      return;
    }

    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/5ad02f70-438a-49a8-8c46-39e994f7e605',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SupportPage.tsx:40',message:'Calling sendMessage',data:{inputTrimmed:input.trim(),isAuthenticated,userEmail:user?.email},"timestamp":Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    sendMessage(input.trim(), isAuthenticated ? user?.email : undefined);
    setInput('');
  };

  const handleRatingSubmit = async () => {
    if (!rating || !sessionId || submittingRating) return;
    
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
      }, 1500);
    } catch (error) {
      console.error('Failed to submit rating:', error);
      setSubmittingRating(false);
      // Show error message to user
      alert('Failed to submit rating. Please try again.');
    }
  };

  const handleRatingDismiss = () => {
    // Mark rating as dismissed to prevent showing again
    if (sessionId) {
      const ratingKey = `rating_submitted_${sessionId}`;
      sessionStorage.setItem(ratingKey, 'dismissed');
    }
    setShowRating(false);
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

        {/* Rating Widget */}
        {showRating && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
              <Bot className="h-4 w-4 text-gray-600" />
            </div>
            <div className={clsx(
              "rounded-2xl px-4 py-3 max-w-[70%] transition-colors",
              ratingSubmitted 
                ? "bg-green-50 border border-green-200" 
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
                  <div className="flex items-center space-x-1 mb-3">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => setRating(star)}
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
                    onChange={(e) => setRatingComment(e.target.value)}
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
