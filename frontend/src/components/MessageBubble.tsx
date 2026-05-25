import type { ChatMessage } from '../types'
import OrderConfirmationCard from './OrderConfirmationCard'

interface Props {
  message: ChatMessage
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex items-end gap-3 px-4 py-1.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
          isUser
            ? 'bg-brand-500 text-white'
            : 'bg-brand-600 text-white'
        }`}
        aria-hidden="true"
      >
        {isUser ? 'U' : 'A'}
      </div>

      {/* Bubble + order card */}
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div
          className={`px-4 py-2.5 rounded-2xl shadow-sm ${
            isUser
              ? 'bg-brand-600 text-white rounded-br-sm'
              : 'bg-white border border-gray-200 text-gray-900 rounded-bl-sm'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.text}
          </p>
        </div>

        {message.orderConfirmation && (
          <div className="w-full">
            <OrderConfirmationCard order={message.orderConfirmation} />
          </div>
        )}

        <time
          dateTime={message.timestamp.toISOString()}
          className="text-xs text-gray-400 px-1"
        >
          {formatTime(message.timestamp)}
        </time>
      </div>
    </div>
  )
}
