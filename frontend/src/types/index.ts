// ─── A2A Protocol types ───────────────────────────────────────────────────────

export interface A2ATextPart {
  kind: 'text'
  text: string
}

export interface A2ADataPart {
  kind: 'data'
  data: Record<string, unknown>
}

export type A2APart = A2ATextPart | A2ADataPart

export interface A2AMessage {
  role: 'user' | 'agent'
  messageId: string
  parts: A2APart[]
  taskId?: string
  contextId?: string
}

export interface A2ATask {
  id: string
  contextId?: string
  status?: {
    state: string
    message?: A2AMessage
  }
  artifacts?: Array<{
    artifactId?: string
    parts: A2APart[]
  }>
  history?: A2AMessage[]
}

export interface JsonRpcResponse {
  jsonrpc: '2.0'
  id: string
  result?: A2ATask | A2AMessage
  error?: {
    code: number
    message: string
    data?: unknown
  }
}

// ─── Domain types ─────────────────────────────────────────────────────────────

export type OrderStatus = 'confirmed' | 'failed' | 'pending_review' | string

export interface OrderConfirmation {
  order_id: string
  status: OrderStatus
  customer_name?: string
  product_name?: string
  quantity?: number
  unit_price?: number
  total_amount?: number
  currency?: string
  transaction_id?: string
  tracking_id?: string
  estimated_delivery?: string
  failure_reason?: string
  correlation_id?: string
}

// ─── Audit trail ──────────────────────────────────────────────────────────────

export interface AuditStep {
  layer: string
  summary: string
  timestamp?: string
}

// ─── Chat UI types ────────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: MessageRole
  text: string
  orderConfirmation?: OrderConfirmation
  auditSteps?: AuditStep[]
  correlationId?: string
  timestamp: Date
}

export interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  taskId?: string
  contextId?: string
  error?: string
}
