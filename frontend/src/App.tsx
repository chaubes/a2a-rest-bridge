import { useChat } from './hooks/useChat'
import ChatWindow from './components/ChatWindow'
import AuditTrailPanel from './components/AuditTrailPanel'

export default function App() {
  const { messages, isLoading, error, send, clearError } = useChat()

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* App header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">
              AgentCart
            </h1>
            <p className="text-xs text-gray-500">
              Order anything — describe it in plain language
            </p>
          </div>

          {/* Audit trail toggle lives in the header row on desktop */}
          <AuditTrailPanel messages={messages} />
        </div>
      </header>

      {/* Chat surface */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full flex flex-col bg-white shadow-sm">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            error={error}
            onSend={send}
            onClearError={clearError}
          />
        </div>
      </main>
    </div>
  )
}
