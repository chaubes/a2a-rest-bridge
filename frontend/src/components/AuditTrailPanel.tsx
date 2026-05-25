import { useState } from 'react'
import type { AuditStep, ChatMessage } from '../types'

interface Props {
  messages: ChatMessage[]
}

function layerColor(layer: string): string {
  const l = layer.toLowerCase()
  if (l.includes('rest') || l.includes('service')) return 'bg-purple-500'
  if (l.includes('mcp') || l.includes('tool')) return 'bg-amber-500'
  if (l.includes('agent') || l.includes('a2a')) return 'bg-brand-500'
  return 'bg-gray-400'
}

function layerLabel(layer: string): string {
  const l = layer.toLowerCase()
  if (l.includes('rest') || l.includes('service')) return 'REST'
  if (l.includes('mcp') || l.includes('tool')) return 'MCP'
  if (l.includes('agent') || l.includes('a2a')) return 'Agent'
  return layer
}

interface StepRowProps {
  step: AuditStep
  index: number
}

function StepRow({ step, index }: StepRowProps) {
  return (
    <li className="flex gap-3 items-start py-2 border-b border-gray-100 last:border-0">
      <div className="flex flex-col items-center flex-shrink-0 pt-1">
        <div
          className={`w-2 h-2 rounded-full ${layerColor(step.layer)}`}
          aria-hidden="true"
        />
        <span className="sr-only">Step {index + 1}</span>
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span
            className={`text-xs font-semibold uppercase tracking-wide ${layerColor(step.layer).replace('bg-', 'text-')}`}
          >
            {layerLabel(step.layer)}
          </span>
          {step.timestamp && (
            <span className="text-xs text-gray-400">{step.timestamp}</span>
          )}
        </div>
        <p className="text-xs text-gray-700 leading-relaxed break-words">
          {step.summary}
        </p>
      </div>
    </li>
  )
}

export default function AuditTrailPanel({ messages }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  // Collect all audit data from assistant messages
  const allSteps: AuditStep[] = messages.flatMap(
    (m) => (m.role === 'assistant' && m.auditSteps) ? m.auditSteps : [],
  )

  // Latest correlation ID
  const latestCorrelationId = [...messages]
    .reverse()
    .find((m) => m.role === 'assistant' && m.correlationId)?.correlationId

  const hasData = allSteps.length > 0 || !!latestCorrelationId

  return (
    <>
      {/* Toggle button — always visible at bottom-right on mobile, side on desktop */}
      <button
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        aria-expanded={isOpen}
        aria-controls="audit-trail-panel"
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors
          ${isOpen
            ? 'bg-brand-100 text-brand-700 hover:bg-brand-200'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}
        `}
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
            d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"
          />
        </svg>
        Audit trail
        {hasData && (
          <span className="w-1.5 h-1.5 rounded-full bg-brand-500 flex-shrink-0" aria-hidden="true" />
        )}
      </button>

      {/* Slide-in panel */}
      {isOpen && (
        <div
          id="audit-trail-panel"
          role="complementary"
          aria-label="Audit trail panel"
          className="
            fixed inset-y-0 right-0 z-40 w-80 bg-white border-l border-gray-200 shadow-2xl
            flex flex-col overflow-hidden
            sm:w-96
          "
        >
          {/* Panel header */}
          <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 flex-shrink-0">
            <h2 className="text-sm font-semibold text-gray-900">Audit Trail</h2>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close audit trail"
              className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded"
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
                  d="M6 18 18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
            {/* Correlation ID */}
            {latestCorrelationId ? (
              <section aria-labelledby="correlation-heading">
                <h3
                  id="correlation-heading"
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2"
                >
                  Active Correlation ID
                </h3>
                <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                  <p className="font-mono text-xs text-gray-800 break-all">
                    {latestCorrelationId}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Use this ID to trace the order across all three layers
                    (Agent → MCP → REST).
                  </p>
                </div>
              </section>
            ) : (
              <div className="bg-gray-50 border border-dashed border-gray-200 rounded-lg px-3 py-3">
                <p className="text-xs text-gray-500">
                  Correlation ID will appear here once an order is processed.
                </p>
              </div>
            )}

            {/* Legend */}
            <section aria-labelledby="legend-heading">
              <h3
                id="legend-heading"
                className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2"
              >
                Layer legend
              </h3>
              <ul className="space-y-1">
                {[
                  { color: 'bg-brand-500', name: 'Agent (Layer 1 — A2A/LangGraph)' },
                  { color: 'bg-amber-500', name: 'MCP (Layer 2 — tool servers)' },
                  { color: 'bg-purple-500', name: 'REST (Layer 3 — Spring Boot APIs)' },
                ].map(({ color, name }) => (
                  <li key={name} className="flex items-center gap-2 text-xs text-gray-600">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${color}`} aria-hidden="true" />
                    {name}
                  </li>
                ))}
              </ul>
            </section>

            {/* Steps */}
            {allSteps.length > 0 ? (
              <section aria-labelledby="steps-heading">
                <h3
                  id="steps-heading"
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2"
                >
                  Steps ({allSteps.length})
                </h3>
                <ul className="divide-y divide-gray-100" aria-label="Audit steps">
                  {allSteps.map((step, i) => (
                    <StepRow key={i} step={step} index={i} />
                  ))}
                </ul>
              </section>
            ) : (
              <div className="bg-gray-50 border border-dashed border-gray-200 rounded-lg px-3 py-3">
                <p className="text-xs text-gray-500">
                  No step-level trace data was returned by the agent. If your
                  agent exposes step details in{' '}
                  <code className="font-mono bg-gray-100 px-1 rounded">
                    task.metadata.audit_steps
                  </code>{' '}
                  they will appear here automatically.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backdrop on mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 sm:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}
    </>
  )
}
