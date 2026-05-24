import { useEffect, useRef, useState, type KeyboardEvent, type FormEvent } from 'react'
import type { ChatMessage } from '../types'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'

const EXAMPLE_PROMPTS = [
  "I want 3 blue widgets delivered to 12 Main St. I'm customer C-001, charge card tok-test-visa.",
  'Order 2 red sprockets for customer C-002. My payment token is tok-test-mc.',
  'Can you place an order for 5 gear sets? Customer ID C-003, card tok-test-amex.',
]

interface EmptyStateProps {
  onPromptClick: (prompt: string) => void
}

function EmptyState({ onPromptClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center">
      <div className="w-16 h-16 rounded-2xl bg-brand-100 flex items-center justify-center mb-5">
        <svg
          className="w-8 h-8 text-brand-600"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"
          />
        </svg>
      </div>
      <h2 className="text-lg font-semibold text-gray-900 mb-2">
        Place an order in plain language
      </h2>
      <p className="text-sm text-gray-500 max-w-xs mb-8">
        Describe what you want and the agent handles inventory check, payment,
        and shipping coordination automatically.
      </p>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">
        Try an example
      </p>
      <ul className="space-y-2 w-full max-w-sm" role="list">
        {EXAMPLE_PROMPTS.map((prompt) => (
          <li key={prompt}>
            <button
              type="button"
              onClick={() => onPromptClick(prompt)}
              className="w-full text-left px-4 py-3 rounded-xl border border-gray-200 bg-white text-sm text-gray-700 hover:border-brand-300 hover:bg-brand-50 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {prompt}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  error?: string
  onSend: (text: string) => void
  onClearError: () => void
}

export default function ChatWindow({
  messages,
  isLoading,
  error,
  onSend,
  onClearError,
}: Props) {
  const [inputValue, setInputValue] = useState('')
  const listRef = useRef<HTMLUListElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  function handleSubmit(e?: FormEvent) {
    e?.preventDefault()
    const text = inputValue.trim()
    if (!text || isLoading) return
    onSend(text)
    setInputValue('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  function handlePromptClick(prompt: string) {
    setInputValue(prompt)
    inputRef.current?.focus()
  }

  const canSend = inputValue.trim().length > 0 && !isLoading

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <EmptyState onPromptClick={handlePromptClick} />
        ) : (
          <ul
            ref={listRef}
            aria-label="Conversation"
            aria-live="polite"
            aria-atomic="false"
            className="py-4 space-y-1"
          >
            {messages.map((msg) => (
              <li key={msg.id}>
                <MessageBubble message={msg} />
              </li>
            ))}
            {isLoading && (
              <li aria-label="Agent is typing">
                <TypingIndicator />
              </li>
            )}
          </ul>
        )}
        <div ref={bottomRef} aria-hidden="true" />
      </div>

      {/* Error banner */}
      {error && (
        <div
          role="alert"
          className="mx-4 mb-2 px-4 py-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3"
        >
          <svg
            className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
            />
          </svg>
          <p className="text-sm text-red-700 flex-1">{error}</p>
          <button
            type="button"
            onClick={onClearError}
            aria-label="Dismiss error"
            className="text-red-400 hover:text-red-600 flex-shrink-0"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18 18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white px-4 py-3">
        <form
          onSubmit={handleSubmit}
          className="flex items-end gap-3"
          aria-label="Send a message"
        >
          <label htmlFor="chat-input" className="sr-only">
            Message the order agent
          </label>
          <textarea
            id="chat-input"
            ref={inputRef}
            rows={1}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Describe your order… (Enter to send, Shift+Enter for newline)"
            aria-describedby={error ? 'chat-error' : undefined}
            className="
              flex-1 resize-none rounded-xl border border-gray-300 bg-gray-50 px-4 py-2.5
              text-sm text-gray-900 placeholder-gray-400
              focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed
              max-h-32 overflow-y-auto
            "
            style={{ height: 'auto' }}
            onInput={(e) => {
              const el = e.currentTarget
              el.style.height = 'auto'
              el.style.height = `${el.scrollHeight}px`
            }}
          />
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send message"
            className="
              flex-shrink-0 w-10 h-10 rounded-xl bg-brand-600 text-white
              flex items-center justify-center
              hover:bg-brand-700 active:bg-brand-800
              focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-colors
            "
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
              />
            </svg>
          </button>
        </form>
        <p className="mt-1.5 text-xs text-gray-400 text-center">
          Enter to send &middot; Shift+Enter for newline
        </p>
      </div>
    </div>
  )
}
