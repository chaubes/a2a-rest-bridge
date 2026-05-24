import { v4 as uuidv4 } from 'uuid'
import type {
  A2ATask,
  A2AMessage,
  AuditStep,
  JsonRpcResponse,
  OrderConfirmation,
} from '../types'

const BASE_URL: string =
  (import.meta.env.VITE_ORDER_AGENT_URL as string | undefined) ??
  'http://localhost:10010'

// ─── JSON-RPC request builder ─────────────────────────────────────────────────

function buildSendRequest(
  userText: string,
  taskId?: string,
  contextId?: string,
): object {
  const params: Record<string, unknown> = {
    message: {
      role: 'user',
      messageId: uuidv4(),
      parts: [{ kind: 'text', text: userText }],
    },
  }

  if (taskId) params.taskId = taskId
  if (contextId) params.contextId = contextId

  return {
    jsonrpc: '2.0',
    id: uuidv4(),
    method: 'message/send',
    params,
  }
}

// ─── Response parsing ─────────────────────────────────────────────────────────

/**
 * Try to parse an OrderConfirmation from a raw object.
 * Returns undefined if the object does not look like a confirmation.
 */
function tryParseOrderConfirmation(
  raw: unknown,
): OrderConfirmation | undefined {
  if (!raw || typeof raw !== 'object') return undefined
  const obj = raw as Record<string, unknown>
  if (typeof obj.order_id !== 'string' && typeof obj.status !== 'string') {
    return undefined
  }
  return {
    order_id: String(obj.order_id ?? ''),
    status: String(obj.status ?? 'unknown'),
    customer_name:
      typeof obj.customer_name === 'string' ? obj.customer_name : undefined,
    product_name:
      typeof obj.product_name === 'string' ? obj.product_name : undefined,
    quantity: typeof obj.quantity === 'number' ? obj.quantity : undefined,
    unit_price: typeof obj.unit_price === 'number' ? obj.unit_price : undefined,
    total_amount:
      typeof obj.total_amount === 'number' ? obj.total_amount : undefined,
    currency: typeof obj.currency === 'string' ? obj.currency : undefined,
    transaction_id:
      typeof obj.transaction_id === 'string' ? obj.transaction_id : undefined,
    tracking_id:
      typeof obj.tracking_id === 'string' ? obj.tracking_id : undefined,
    estimated_delivery:
      typeof obj.estimated_delivery === 'string'
        ? obj.estimated_delivery
        : undefined,
    failure_reason:
      typeof obj.failure_reason === 'string' ? obj.failure_reason : undefined,
    correlation_id:
      typeof obj.correlation_id === 'string' ? obj.correlation_id : undefined,
  }
}

/**
 * Scan a text string for a fenced ```json … ``` block and try to parse
 * an OrderConfirmation from it.
 */
function extractOrderFromTextBlock(text: string): OrderConfirmation | undefined {
  const fenceRe = /```(?:json)?\s*([\s\S]*?)```/g
  let match: RegExpExecArray | null
  while ((match = fenceRe.exec(text)) !== null) {
    try {
      const parsed: unknown = JSON.parse(match[1])
      const oc = tryParseOrderConfirmation(parsed)
      if (oc) return oc
    } catch {
      // not valid JSON — keep scanning
    }
  }
  return undefined
}

// ─── Audit step extraction ────────────────────────────────────────────────────

/**
 * Pull any audit / step information out of the raw task response.
 * The A2A spec does not define a canonical field; we probe several candidates.
 */
function extractAuditSteps(task: A2ATask): AuditStep[] {
  const steps: AuditStep[] = []

  // candidate 1: task.metadata.audit_steps or task.metadata.steps
  const meta = (task as unknown as Record<string, unknown>).metadata
  if (meta && typeof meta === 'object') {
    const metaObj = meta as Record<string, unknown>
    const candidates = [
      metaObj.audit_steps,
      metaObj.steps,
      metaObj.audit_trail,
    ]
    for (const c of candidates) {
      if (Array.isArray(c)) {
        for (const item of c) {
          if (item && typeof item === 'object') {
            const s = item as Record<string, unknown>
            steps.push({
              layer: String(s.layer ?? s.name ?? 'agent'),
              summary: String(s.summary ?? s.message ?? s.description ?? ''),
              timestamp: typeof s.timestamp === 'string' ? s.timestamp : undefined,
            })
          }
        }
        if (steps.length) return steps
      }
    }
  }

  // candidate 2: scan history messages for role=tool or role=system
  if (Array.isArray(task.history)) {
    for (const msg of task.history) {
      const m = msg as A2AMessage & { role: string }
      if (m.role !== 'user' && m.role !== 'agent') {
        const texts = (m.parts ?? [])
          .filter((p) => p.kind === 'text')
          .map((p) => (p as { kind: 'text'; text: string }).text)
          .join(' ')
        if (texts) {
          steps.push({ layer: m.role, summary: texts })
        }
      }
    }
  }

  return steps
}

// ─── Main response parser ─────────────────────────────────────────────────────

export interface ParsedAgentResponse {
  text: string
  orderConfirmation?: OrderConfirmation
  auditSteps: AuditStep[]
  taskId?: string
  contextId?: string
  correlationId?: string
}

function parseAgentResponse(task: A2ATask): ParsedAgentResponse {
  const textParts: string[] = []
  let orderConfirmation: OrderConfirmation | undefined

  // Gather parts from: task.status.message, task.artifacts, task.history (last agent message)
  const partSources: Array<{ parts?: unknown[] }> = []

  if (task.status?.message) {
    partSources.push(task.status.message)
  }

  if (Array.isArray(task.artifacts)) {
    for (const artifact of task.artifacts) {
      partSources.push(artifact)
    }
  }

  if (Array.isArray(task.history)) {
    const agentMessages = task.history.filter(
      (m) => (m as A2AMessage).role === 'agent',
    )
    if (agentMessages.length > 0) {
      partSources.push(agentMessages[agentMessages.length - 1])
    }
  }

  for (const source of partSources) {
    if (!Array.isArray(source.parts)) continue
    for (const part of source.parts) {
      if (!part || typeof part !== 'object') continue
      const p = part as Record<string, unknown>

      if (p.kind === 'text' && typeof p.text === 'string') {
        textParts.push(p.text)
        if (!orderConfirmation) {
          orderConfirmation = extractOrderFromTextBlock(p.text)
        }
      } else if (p.kind === 'data' && p.data && typeof p.data === 'object') {
        const oc = tryParseOrderConfirmation(p.data)
        if (oc && !orderConfirmation) {
          orderConfirmation = oc
        }
      }
    }
  }

  const auditSteps = extractAuditSteps(task)
  const correlationId =
    orderConfirmation?.correlation_id ??
    (
      (task as unknown as Record<string, unknown>).metadata as
        | Record<string, unknown>
        | undefined
    )?.correlation_id as string | undefined

  return {
    text:
      textParts.join('\n\n').trim() ||
      'The agent processed your request but returned no message.',
    orderConfirmation,
    auditSteps,
    taskId: task.id,
    contextId: task.contextId,
    correlationId,
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────

export async function sendMessage(
  userText: string,
  taskId?: string,
  contextId?: string,
): Promise<ParsedAgentResponse> {
  const body = buildSendRequest(userText, taskId, contextId)

  let resp: Response
  try {
    resp = await fetch(`${BASE_URL}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch (err) {
    const msg =
      err instanceof Error ? err.message : 'Network request failed'
    throw new Error(`Cannot reach the order agent: ${msg}`)
  }

  if (!resp.ok) {
    throw new Error(
      `Order agent returned HTTP ${resp.status}: ${resp.statusText}`,
    )
  }

  let json: JsonRpcResponse
  try {
    json = (await resp.json()) as JsonRpcResponse
  } catch {
    throw new Error('Order agent returned a non-JSON response')
  }

  if (json.error) {
    throw new Error(
      `Agent error (${json.error.code}): ${json.error.message}`,
    )
  }

  if (!json.result) {
    throw new Error('Agent returned a JSON-RPC response with no result')
  }

  // The result can be an A2ATask or a bare A2AMessage.
  // If it lacks task-like fields, wrap it into a minimal task shape.
  const raw = json.result as unknown as Record<string, unknown>
  let task: A2ATask

  if (typeof raw.id === 'string' && (raw.status || raw.artifacts || raw.history)) {
    // Looks like a task
    task = raw as unknown as A2ATask
  } else if (raw.role || raw.parts) {
    // Bare message — wrap it
    task = {
      id: (raw.messageId as string | undefined) ?? uuidv4(),
      contextId: raw.contextId as string | undefined,
      status: {
        state: 'completed',
        message: raw as unknown as A2AMessage,
      },
    }
  } else {
    // Unknown shape — try treating as task anyway
    task = raw as unknown as A2ATask
  }

  return parseAgentResponse(task)
}
