export default function TypingIndicator() {
  return (
    <div
      role="status"
      aria-label="Agent is typing"
      className="flex items-end gap-3 px-4 py-2"
    >
      {/* Avatar placeholder */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center">
        <span className="text-white text-xs font-bold" aria-hidden="true">
          A
        </span>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1.5 items-center h-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="block w-2 h-2 rounded-full bg-gray-400 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
              aria-hidden="true"
            />
          ))}
        </div>
      </div>
    </div>
  )
}
