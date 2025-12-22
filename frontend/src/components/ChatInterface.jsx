import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import './ChatInterface.css';

// Copy button component
function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <button
      className={`copy-btn ${copied ? 'copied' : ''}`}
      onClick={handleCopy}
      title={copied ? 'Copied!' : label}
      data-testid="copy-btn"
    >
      {copied ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      )}
      <span>{copied ? 'Copied!' : label}</span>
    </button>
  );
}

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
      </div>
    );
  }

  // Helper to check if a stage is actively loading (not just has loading flag)
  // A stage is loading ONLY if loading flag is true AND data hasn't arrived yet
  const isStageLoading = (msg, stage) => {
    const loadingFlag = msg.loading?.[stage];
    const hasData = stage === 'stage1' ? msg.stage1 : stage === 'stage2' ? msg.stage2 : msg.stage3;
    return loadingFlag && !hasData;
  };

  return (
    <div className="chat-interface" data-testid="chat-interface">
      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <h2>Start a conversation</h2>
            <p>Ask a question to consult the LLM Council</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">You</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Council</div>

                  {/* Stage 1 - Show loading ONLY if no data yet */}
                  {isStageLoading(msg, 'stage1') && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 1: Collecting individual responses...</span>
                    </div>
                  )}
                  {msg.stage1 && msg.stage1.length > 0 && <Stage1 responses={msg.stage1} />}

                  {/* Stage 2 - Show loading ONLY if no data yet */}
                  {isStageLoading(msg, 'stage2') && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 2: Models ranking each other...</span>
                    </div>
                  )}
                  {msg.stage2 && msg.stage2.length > 0 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {/* Stage 3 - Show loading ONLY if no data yet */}
                  {isStageLoading(msg, 'stage3') && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Stage 3: Synthesizing final answer...</span>
                    </div>
                  )}
                  {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Always show input form when conversation is selected */}
      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="message-input"
          placeholder={
            conversation.messages.length === 0
              ? "Ask your question... (Enter to send, Shift+Enter for new line)"
              : "Continue the conversation... (Enter to send)"
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          data-testid="message-input"
        />
        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || isLoading}
          data-testid="send-button"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}

// Export CopyButton for use in other components
export { CopyButton };
